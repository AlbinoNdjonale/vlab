from datetime import datetime
from random import randint
import socket
from typing import Protocol as Interface, TypeAlias, TypedDict, Literal

from vlab.use_protocol import Protocol

class Comunication(Interface):
    def start_connection(self): ...
    def receive_message(self) -> bytes: ...
    def send_message(self, message: bytes) -> bool: ...
    def close(self) -> None: ...

class Sample(TypedDict):
    id: str

ApparatusMode: TypeAlias = Literal['P', 'T', 'D']
Command: TypeAlias = Literal['query', 'set_sample']

class Apparatus:
    def __init__(
        self,
        protocol: Protocol,
        comunication: Comunication,
        device_name: str,
        supplier: str,
        app_receive: str,
        facility_receive: str,
        mode: ApparatusMode = 'P',
        token: str = ''
    ) -> None:
        self.__device_name      = device_name
        self.__supplier         = supplier
        self.__app_receive      = app_receive
        self.__facility_receive = facility_receive

        self.__samples: list[Sample] = []

        self.__unique_identifiers: list[str] = []

        self.__protocol: Protocol = protocol
        self.__comunication = comunication 
        self.__comunication.start_connection()

        self.__mode = mode
        self.__token = token

    def put_on_rack(self, *samples: Sample):
        self.__samples.extend(samples)

    def exec(self, command: Command, *params):
        match command:
            case 'set_sample':
                if len(params) == 0: return 'Informe o ID da amostra'
                self.__samples.append({
                    'id': params[0]
                })

                return f"Amostra com ID '{params[0]}' adicionado na rack"
            case 'query':
                if not self.__samples: return 'Sem amostras na rack'

                for sample in self.__samples:
                   message = self.__protocol.create_query_worklist(
                        device_name      = self.__device_name,
                        supplier         = self.__supplier,
                        app_receive      = self.__app_receive,
                        facility_receive = self.__facility_receive,
                        datetime         = self.__protocol.format_date(datetime.now()),
                        token            = self.__token,
                        mode             = self.__mode,
                        sample_id        = sample['id'],
                        query_id         = self.generate_unique_identifier('Q'),
                        message_id       = self.generate_unique_identifier(),
                        priority         = 'I'
                    ) 

                   sucess = self.__comunication.send_message(message)

                   return f'Perguntando ao sistema o que fazer com a amostra {sample["id"]}'\
                        if sucess else 'Erro ao enviar mensagem'

    def receive_message(self) -> bytes:
        return self.__comunication.receive_message()

    def generate_unique_identifier(self, prefix = '') -> str:
        while True:
            identifier = prefix+str(randint(0, 9999)).zfill(4)

            if identifier not in self.__unique_identifiers:
                self.__unique_identifiers.append(identifier)
                return identifier

    def close(self):
        self.__comunication.close()
