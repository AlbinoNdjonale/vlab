from datetime import datetime

from vlab.use_protocol import Protocol

import socket
from typing import (
    Callable,
    Literal,
    NotRequired,
    Protocol as Interface,
    TypeAlias,
    TypedDict
)

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
    name: NotRequired[str]
    protocol: NotRequired[Literal['HL7', 'ASTM']]
    has_contract: bool
    id: int

class Gateway:
    def __init__(
        self,
        hl7_protocol: Protocol,
        astm_protocol: Protocol,
        mode: ModeProcessing = 'P'
    ) -> None:
        self.__clients: list[Client] = []
        self.__links: dict[Mode, Link] = {}

        self.__hl7  = hl7_protocol
        self.__astm = astm_protocol

        self.__mode = mode

        self.__next_client_id = 0
    
    @property
    def get_connn(self) -> socket.socket|None: ...

    def add_client(self, client_conn: Comunication, address: str) -> int:
        self.__next_client_id += 1

        self.__clients.append({
            'conn': client_conn,
            'address': address,
            'has_contract': False,
            'id': self.__next_client_id
        })

        return self.__next_client_id

    def get_client(
        self,
        id: int|str,
        by: Literal['id', 'address'] = 'id'
    ) -> Client|None:
        for clinet in self.__clients:
            if clinet[by] == id:
                return clinet

        return None

    @property
    def get_devices(self) -> list[Client]:
        return self.__clients

    @property
    def apparatus_config(self):
        return ApparatusConfig

    def protocol(self, protocol_name: Literal['HL7', 'ASTM']) -> Protocol:
        return self.__hl7 if protocol_name == 'HL7' else self.__astm

    def receive_message(self, message: bytes, client_id: int):
        client = self.get_client(client_id)

        if client is None:
            return

        apparatus_config = ApparatusConfig(client['address'])

        if (protocol_name := apparatus_config.protocol) is None:
            return

        if client.get('protocol') is None:
            client['protocol'] = protocol_name

        protocol = self.protocol(protocol_name)

        message_decode = protocol.parser(message)

        if message_decode is None: return
        
        message_decode_json = message_decode['json']
        headers = message_decode_json['headers']

        apparatus = f'{headers["device_name"]}_{headers["supplier"]}'

        apparatus_config.set_apparatus(apparatus)

        client['has_contract'] = apparatus_config.has_contract

        if client.get('name') is None:
            client['name'] = apparatus 

        message_strucuture = message_decode['json']\
            ['headers']['message_type']['message_structure']

        lis_server = LisServer()

        response_message: bytes|None = None

        match apparatus_config.message_codes.get(message_strucuture):
            case 'query_exam_orders':
                params_base = {
                    'app_receive': headers['app_receive'],
                    'facility_receive': headers['facility_receive'],
                    'device_name': headers['device_name'],
                    'supplier': headers['supplier'],
                    'datetime': protocol.format_date(datetime.now()),
                    'message_id': str(datetime.now().timestamp())[12:],
                    'mode': self.__mode,
                    'requisition_message_id': headers['message_id'],
                    'requisition_query_id': message_decode_json['query_id']
                }
                
                error, exam_orders = lis_server.exam_orders(message_decode_json)

                if error:
                    response_message = protocol.create_order_exame(
                        **params_base,   
                        message_processing_status = 'AE',
                        query_result_status = 'AE'
                    )

                elif exam_orders is None:
                    response_message = protocol.create_order_exame(
                        **params_base,
                        message_processing_status = 'AA',
                        query_result_status = 'NF'
                    )
                else:
                    esq = message_decode_json['equipment_standard_query']

                    patient = exam_orders.get('patient', {})

                    response_message = protocol.create_order_exame(
                        **params_base,
                        message_processing_status = 'AA',
                        query_result_status = 'OK',
                        esq_id = esq['identifier'],
                        esq_description = esq['description'],
                        esq_codibg_system = esq['coding_system'],
                        patient_id = patient.get('id') or '',
                        paient_name = patient.get('name') or '',
                        patient_last_name = patient.get('last_name') or '',
                        patient_gender = patient.get('gender') or '',
                        patient_birth = patient.get('birth') or '',
                        exame_orders = exam_orders.get('exam_orders') or [],
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
