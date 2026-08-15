import socket
from typing import TypeAlias, Literal

Mode: TypeAlias = Literal['CLIENT', 'SERVER']

class InterfaceTcpIp:
    def __init__(
        self,
        mode: Mode|None = None,
        port: int|None = None,
        host: str|None = None,
        client: socket.socket|None = None,
        multi_client: bool = False
    ) -> None:
        self.__server: socket.socket|None = None
        self.__client_connection = client
        
        self.__host = '0.0.0.0' if mode == 'SERVER' else host
        self.__port = port

        self.__mode: Mode|None = mode

        self.__multi_client = multi_client

    def start_connection(self):
        self.__server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        if self.__mode == 'SERVER':
            self.__server.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            if self.__multi_client:
                self.__server.setblocking(False)

            self.__server.bind((self.__host, self.__port))

            self.__server.listen(socket.SOMAXCONN if self.__multi_client else 1)

            if not self.__multi_client:
                self.__client_connection, _ = self.__server.accept()

        else:
            self.__client_connection = self.__server
            self.__client_connection.connect((self.__host, self.__port))

    @property
    def get_conn(self) -> socket.socket|None:
        return self.__server if self.__server else self.__client_connection

    @property
    def get_bytes(self):
        return 1024

    @property
    def get_mode(self):
        return self.__mode

    def receive_message(self) -> bytes:
        if self.__client_connection is None:
            raise Exception('No Client connected')

        return self.__client_connection.recv(self.get_bytes)

    def send_message(self, message: bytes):
        if self.__client_connection is None:
            raise Exception('No Client connected')
        
        try:
            return self.__client_connection.sendall(message) is None
        except:
            return False

    def close(self):
        if self.__client_connection is None and self.__server is None:
            raise Exception('No Client connected')

        if self.__client_connection is not None:
            self.__client_connection.shutdown(socket.SHUT_RDWR)
            self.__client_connection.close()
        
        if (not self.__server == self.__client_connection) and self.__server is not None:
            self.__server.shutdown(socket.SHUT_RDWR)
            self.__server.close()
