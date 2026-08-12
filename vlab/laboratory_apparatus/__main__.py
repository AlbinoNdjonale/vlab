import asyncio
from vlab.use_protocol import Protocol

from vlab.comunication import InterfaceSerial, InterfaceTcpIp
from vlab.utils import Utils

from .apparatus import Apparatus
from vlab.nursery import Nursery

async def send_message(apparatus: Apparatus, nursery: Nursery):
    while True:
        command = (await asyncio.to_thread(input, '-> ')).split(' ')

        response = None

        match command[0]:
            case 'q':
                nursery.stop_all_tasks()
            case 'set_sample':
                response = apparatus.exec(command[0], *command[1:])
            case 'query':
                response = apparatus.exec(command[0], *command[1:])
            
        if response is not None:
            print(f'{response}\n')

async def receive_message(apparatus: Apparatus, nursery: Nursery):
    while True:
        message = await asyncio.to_thread(apparatus.receive_message)

        if not message:
            nursery.stop_all_tasks()
            break

        print(f'\nMensagem: {message}')
        
        print('\nEsperando: ...\n-> ', end = '')

async def main():
    config = Utils.read_config()

    mode = 'SERVER' if config['APPARATUS_AS_SERVER'] else 'CLIENT'

    apparatus = Apparatus(
        Protocol(config['PROTOCOL']),
        InterfaceSerial(
            port     = config['APPARATUS_SERIAL_PORT'],
            baudrate = config.get('BAUDRATE', 9600),
            bytesize = config.get('BYTESIZE', 8),
            parity   = config.get('PARITY', 'N'),
            stopbits = config.get('STOPBITS', 1)
        ) if config['SERIAL_MODE'] else InterfaceTcpIp(
            mode = mode,
            port = config['APPARATUS_TCP_PORT']\
                if mode == 'SERVER' else config['AGENT_TCP_PORT'],
            host = config.get('TCP_HOST', '127.0.0.1')
        ),
        'BC-6200',
        'MINDRAY',
        'LIS_SERVER',
        'LAB_CENTRAL',
        config.get('MODE', 'P')
    )

    async with Nursery() as nursery:
        try:
            nursery.create_task(send_message(apparatus, nursery))
            nursery.create_task(receive_message(apparatus, nursery))
        except:
            nursery.stop_all_tasks()
    
    apparatus.close()

if __name__ == '__main__':
    asyncio.run(main())
