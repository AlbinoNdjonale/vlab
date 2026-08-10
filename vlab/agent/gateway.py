from vlab.use_protocol import Protocol
import socket
from typing import Callable, Literal, Protocol as Interface, TypeAlias

class Comunication(Interface):
    def start_connection(self): ...
    @property
    def get_conn(self) -> socket.socket|None: ...
    def receive_message(self) -> bytes: ...
    def send_message(self, message: bytes) -> bool: ...
    def close(self) -> None: ...

Mode: TypeAlias = Literal[
    'SERIAL', 'SERVER', 'CLIENT'
]

Link: TypeAlias = Callable[..., None]

class Gateway:
    def __init__(self, protocol: Protocol) -> None:
        self.__clients = []
        self.__links: dict[Mode, Link] = {}

        self.__hl7 = protocol
    
    @property
    def get_connn(self) -> socket.socket|None: ...

    def add_client(self, client_conn: Comunication, address: str) -> int:
        id = len(self.__clients) + 1

        self.__clients.append({
            'conn': client_conn,
            'address': address,
            'id': id
        })

        return id

    def receive_message(self, message: bytes, client_id: int):
        print(self.__hl7.parser(message))

    def set_link(self, mode: Mode, link: Link):
        self.__links[mode] = link
