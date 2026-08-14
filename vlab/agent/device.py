import asyncio
import socket
from typing import Any, Protocol

from vlab.use_protocol import Protocol

from vlab.comunication import InterfaceSerial, InterfaceTcpIp
from vlab.utils import Utils, Config

from .gateway import Gateway
from vlab.nursery import Nursery

class DynamicState(Protocol):
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

class HasDynamicState(Protocol):
    state: DynamicState

async def send_message(gateway: Gateway):
    queue = asyncio.Queue()
    gateway.set_link('SERVER', queue.put_nowait)

    while True:
        message_data = await queue.get()
        queue.task_done()

        comunication: InterfaceTcpIp|InterfaceSerial = message_data['comunication']
        message = message_data['message']

        if isinstance(comunication, InterfaceSerial):
            await asyncio.to_thread(lambda: comunication.send_message(message))
        else:
            if comunication.get_mode == 'CLIENT':
                await asyncio.to_thread(lambda: comunication.send_message(message))
            elif (conn := comunication.get_conn):
                await asyncio.get_running_loop().sock_sendall(conn, message)

async def handle_client_server(
    gateway: Gateway,
    comunication: InterfaceTcpIp,
    client_id: int
):
    try:
        while True:
            message = await asyncio.to_thread(comunication.receive_message)
            
            if not message:break

            gateway.receive_message(message, client_id)
    finally:
        comunication.close()

async def handle_client(gateway: Gateway, comunication: InterfaceTcpIp, client_id: int):
    try:
        client = comunication.get_conn
        if client:
            while True:
                message = await asyncio.get_running_loop()\
                    .sock_recv(client, comunication.get_bytes)

                if not message:break

                gateway.receive_message(message, client_id)
    finally:
        comunication.close()

async def handle_client_serial(
    gateway: Gateway,
    comunication: InterfaceSerial,
    client_id: int
):
    try:
        while True:
            message = await asyncio.to_thread(comunication.receive_message)
            
            if not message:break

            gateway.receive_message(message, client_id)
    finally:
        comunication.close()

async def connect_server(gateway: Gateway, config: Config):
    queue = asyncio.Queue()
    gateway.set_link('CLIENT', queue.put_nowait)

    async with Nursery() as nursery:
        while True:
            connect_data = await queue.get()
            queue.task_done()

            comunication = InterfaceTcpIp(
                mode = 'CLIENT',
                port = connect_data.get('port'),
                host = connect_data.get('host')
            )

            comunication.start_connection()

            client_id = gateway.add_client(comunication, connect_data.get('host'))

            nursery.create_task(handle_client_server(gateway, comunication, client_id))

async def connect_serial(gateway: Gateway, config: Config):
    queue = asyncio.Queue()
    gateway.set_link('SERIAL', queue.put_nowait)
    
    async with Nursery() as nursery:
        while True:
            connec_data = await queue.get()
            queue.task_done()

            comunication = InterfaceSerial(
                port     = connec_data.get('port'),
                baudrate = connec_data.get('baudrate', config.get('BAUDRATE', 9600)),
                bytesize = connec_data.get('bytesize', config.get('BYTESIZE', 8)),
                parity   = connec_data.get('parity', config.get('PARITY', 'N')),
                stopbits = connec_data.get('stopbits', config.get('STOPBITS', 1))
            )

            client_id = gateway.add_client(comunication, connec_data.get('port'))

            nursery.create_task(handle_client_serial(gateway, comunication, client_id))

async def start_server_tcp(gateway: Gateway, config: Config):
    loop = asyncio.get_running_loop()

    comunication_server = InterfaceTcpIp(
        mode = 'SERVER',
        port = config['AGENT_TCP_PORT'],
        multi_client = True
    )

    comunication_server.start_connection()

    server = comunication_server.get_conn

    if server:
        async with Nursery() as nursery:
            for _ in Utils.take_numbres(config['GATEWAY_MAX_CLIENT']):
                client_conn, client_address = await loop.sock_accept(server) 
                client_ip: str
                client_ip, _ = client_address
                
                comunication_client = InterfaceTcpIp(client = client_conn)

                client_id = gateway.add_client(comunication_client, client_ip)

                nursery.create_task(handle_client(gateway, comunication_client, client_id))

    comunication_server.close()

async def main(app: HasDynamicState):
    config = Utils.read_config()

    gateway = Gateway(
        Protocol('HL7'),
        Protocol('ASTM'),
        config.get('MODE', 'P')
    )

    app.state.gateway = gateway

    async with Nursery() as nursery:
        nursery.create_task(start_server_tcp(gateway, config))
        nursery.create_task(connect_serial(gateway, config))
        nursery.create_task(send_message(gateway))
