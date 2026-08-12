from datetime import datetime

from vlab.use_protocol import Protocol

import socket
from typing import Callable, Literal, Protocol as Interface, TypeAlias, TypedDict

from .infrastructure.apparatus_config import ApparatusConfig
from .infrastructure.entity.lis_server import LisServer 

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

ModeProcessing: TypeAlias = Literal['P', 'T', 'D']

class Client(TypedDict):
    conn: Comunication
    address: str
    id: int

class Gateway:
    def __init__(self, protocol: Protocol, mode: ModeProcessing = 'P') -> None:
        self.__clients: list[Client] = []
        self.__links: dict[Mode, Link] = {}

        self.__hl7 = protocol

        self.__mode = mode

        self.__next_client_id = 0
    
    @property
    def get_connn(self) -> socket.socket|None: ...

    def add_client(self, client_conn: Comunication, address: str) -> int:
        self.__next_client_id += 1

        self.__clients.append({
            'conn': client_conn,
            'address': address,
            'id': self.__next_client_id
        })

        return self.__next_client_id

    def get_client(self, id: int) -> Client|None:
        for clinet in self.__clients:
            if clinet['id'] == id:
                return clinet

        return None

    def receive_message(self, message: bytes, client_id: int):
        client = self.get_client(client_id)

        if client is None:
            return

        lis_server = LisServer()

        message_decode = self.__hl7.parser(message)

        if message_decode is None: return
        
        message_decode_json = message_decode['json']
        headers = message_decode_json['headers']

        apparatus = f'{headers["device_name"]}_{headers["supplier"]}'

        apparatus_config = ApparatusConfig(apparatus, client['address'])

        message_strucuture = message_decode['json']\
                ['headers']['message_type']['message_structure']

        response_message: bytes|None = None

        match apparatus_config.message_codes.get(message_strucuture):
            case 'query_exam_orders':
                params_base = {
                    'app_receive': headers['app_receive'],
                    'facility_receive': headers['facility_receive'],
                    'device_name': headers['device_name'],
                    'supplier': headers['supplier'],
                    'datetime': self.__hl7.format_date(datetime.now()),
                    'message_id': str(datetime.now().timestamp())[12:],
                    'mode': self.__mode,
                    'requisition_message_id': headers['message_id'],
                    'requisition_query_id': message_decode_json['query_id']
                }
                
                error, exam_orders = lis_server.exam_orders(message_decode_json)

                if error:
                    response_message = self.__hl7.create_order_exame(
                        **params_base,   
                        message_processing_status = 'AE',
                        query_result_status = 'AE'
                    )

                elif exam_orders is None:
                    response_message = self.__hl7.create_order_exame(
                        **params_base,
                        message_processing_status = 'AA',
                        query_result_status = 'NF'
                    )
                else:
                    esq = message_decode_json['equipment_standard_query']

                    patient = exam_orders['patient']

                    response_message = self.__hl7.create_order_exame(
                        **params_base,
                        message_processing_status = 'AA',
                        query_result_status = 'OK',
                        esq_id = esq['identifier'],
                        esq_description = esq['description'],
                        esq_codibg_system = esq['coding_system'],
                        patient_id = patient['id'],
                        paient_name = patient['name'],
                        patient_last_name = patient['last_name'],
                        patient_gender = patient['gender'],
                        patient_birth = patient['birth'],
                        table_coding = apparatus_config.table_coding,
                        exam_sytem = apparatus_config.exame_system
                    )
            case _:
                return
        
        if response_message:
            self.__links['SERVER']({
                'comunication': client['conn'],
                'message': response_message
            })

    def set_link(self, mode: Mode, link: Link):
        self.__links[mode] = link
