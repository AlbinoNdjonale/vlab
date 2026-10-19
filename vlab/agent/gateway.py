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

ProtocolName: TypeAlias = Literal['HL7', 'ASTM']

class Client(TypedDict):
    conn: Comunication
    address: str
    name: NotRequired[str]
    protocol: NotRequired[ProtocolName]
    has_contract: bool
    id: int

class Gateway:
    def __init__(
        self,
        hl7_protocol: Protocol,
        astm_protocol: Protocol,
        url_lis_server: str,
        mode: ModeProcessing = 'P'
    ) -> None:
        self.__clients: list[Client] = []
        self.__links: dict[Mode, Link] = {}

        self.__hl7  = hl7_protocol
        self.__astm = astm_protocol

        self.__mode = mode

        self.__next_client_id = 0

        self.__url_lis_server = url_lis_server
    
    def add_device(self, address: str, port: int|None = None):
        if port: # TCP/IP
            self.__links['CLIENT']({'host': address, 'port': port})
        else: # SERIAL
            self.__links['SERIAL']({'port': address})

    def add_client(self, client_conn: Comunication, address: str) -> int:
        self.__next_client_id += 1
        
        apparatus_config = ApparatusConfig(address)

        client: Client = {
            'conn': client_conn,
            'address': address,
            'has_contract': apparatus_config.has_contract,
            'id': self.__next_client_id
        }

        if (protocol := apparatus_config.protocol):
            client['protocol'] = protocol

        self.__clients.append(client)

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

    def remove_client(self, client_id: int):
        self.__clients = [
            client
            for client in self.__clients if not client['id'] == client_id
        ]

    @property
    def get_devices(self) -> list[Client]:
        return self.__clients

    @property
    def apparatus_config(self):
        return ApparatusConfig
    
    @property
    def lis_server(self):
        lis_server = LisServer()
        lis_server.set_base_url(self.__url_lis_server)
        return lis_server

    def protocol(self, protocol_name: ProtocolName) -> Protocol:
        return self.__hl7 if protocol_name == 'HL7' else self.__astm
    
    def buffer_manager(self, client_id: int):
        while True:
            client = self.get_client(client_id) 
            
            if client:
                protocol = None
                if (protocol_name := client.get('protocol')) is None:
                    apparatus_config = ApparatusConfig(client['address'])

                    if (protocol := apparatus_config.protocol):
                        client['protocol'] = protocol

                if protocol := client.get('protocol'):
                    return (
                        self.__hl7 if protocol == 'HL7' else self.__astm
                    ).buffer_manager

    def send_exam_orders(self, message: dict, client_address: str):
        self.lis_server.insert_lote_exam_orders(message.get('exam_orders', []))
        self.lis_server.save()

        client = self.get_client(client_address, 'address')

        if client is None:
            return

        apparatus_config = ApparatusConfig(client['address'])

        if (protocol_name := apparatus_config.protocol) is None:
            return

        if client.get('protocol') is None:
            client['protocol'] = protocol_name

        protocol = self.protocol(protocol_name)

        device_name, supplier = client.get('name', '_').split('_')

        response_message = protocol.create_lote_order_exam(
            app_receive = message.get('app_id', ''),
            facility_receive = message.get('facility_id', ''),
            device_name = device_name,
            supplier = supplier,
            mode = self.__mode,
            datetime = protocol.format_date(datetime.now()),
            message_id = str(datetime.now().timestamp())[12:],
            table_coding = apparatus_config.table_coding,
            exam_sytem = apparatus_config.exam_system,
            exam_orders = message.get('exam_orders', [])
        ) 

        self.__links['SERVER']({
            'comunication': client['conn'],
            'message': response_message
        })

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

        message_type = headers['message_type'] 

        message_strucuture = message_type.get('message_structure') or\
            f'{message_type.get("message_code")}_{message_type.get("trigger_event")}'

        lis_server = self.lis_server

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
                    'requisition_query_id': message_decode_json['query_id'],
                    'sample_id': message_decode_json['user_params'][0]
                }
                
                error, exam_orders = lis_server.exam_orders(message_decode_json)

                if error:
                    response_message = protocol.create_order_exam(
                        **params_base,   
                        message_processing_status = 'AE',
                        query_result_status = 'AE'
                    )

                elif exam_orders is None:
                    response_message = protocol.create_order_exam(
                        **params_base,
                        message_processing_status = 'AA',
                        query_result_status = 'NF'
                    )
                else:
                    esq = message_decode_json['equipment_standard_query']

                    patient = exam_orders.get('patient', {})

                    response_message = protocol.create_order_exam(
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
                        alternative_patient_id = patient.get('alternative_id') or '',
                        visit_info = exam_orders.get('visit_info') or None,
                        exam_orders = exam_orders.get('exam_orders') or [],
                        table_coding = apparatus_config.table_coding,
                        exam_sytem = apparatus_config.exam_system
                    )
            case 'result_exam_orders':
                results = [
                    {
                        **{
                            key: value
                            for key, value in order.items()
                            if key not in ['id', 'executor_side_id']
                        },
                        'sample_id': (order.get('id') or order.get('executor_side_id')),
                        'observations': [
                            observation
                            for observation in message_decode_json['exam_results']
                            if observation.pop('order_idx') == idx
                        ]
                    }
                    for idx, order in enumerate(message_decode_json['exam_orders'])
                ]

                lis_server.send_results(results)

                lis_server.save()

                response_message = protocol.create_ack(
                     app_receive = headers['app_receive'],
                     facility_receive = headers['facility_receive'],
                     device_name = headers['device_name'],
                     supplier = headers['supplier'],
                     datetime = protocol.format_date(datetime.now()),
                     message_id = str(datetime.now().timestamp())[12:],
                     mode = self.__mode,
                     requisition_message_id = headers['message_id'],
                     detail = 'Exam result receive'
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
