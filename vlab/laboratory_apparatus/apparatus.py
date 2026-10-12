from datetime import datetime
from random import randint
import socket
import time
from typing import cast, Protocol as Interface, TypeAlias, TypedDict, Literal

from vlab.use_protocol import Protocol

class Comunication(Interface):
    def start_connection(self): ...
    def receive_message(self) -> bytes: ...
    def send_message(self, message: bytes) -> bool: ...
    def close(self) -> None: ...

class Observation(TypedDict):
    code: str
    value: str
    type_value: str
    unity: str
    probability: str
    ref_min: str
    ref_max: str

class Sample(TypedDict):
    id: str
    observations: list[Observation]

ApparatusMode: TypeAlias = Literal['P', 'T', 'D']
Command: TypeAlias = Literal['analyze', 'set_sample']

code_desc = {
}

message_codes = {
    'HL7': {
        'RSP_K21': 'exam_orders',
        'ORM_O01': 'lote_exam_orders'
    },
    'ASTM': {

    }
}

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

        self.__exam_orders: dict[str, dict] = {}

    def put_on_rack(self, *samples: Sample):
        self.__samples.extend(samples)

    def exec(self, command: Command, *params: str):
        match command:
            case 'set_sample':
                if len(params) == 0: return 'Informe o ID da amostra'

                self.__samples.append({
                    'id': params[0],
                    'observations': [
                        cast(Observation, {
                            value[0].strip(): value[1].strip()
                            for attr in obs.split(';') if (value := attr.split('='))
                        })
                        for obs in ''.join(params[1:]).replace(' ', '').split('|')
                        if obs
                    ]
                })

                return f"Amostra com ID '{params[0]}' adicionado na rack"
            case 'analyze':
                if not self.__samples: return 'Sem amostras na rack'

                responses: list[str] = []

                params_base = {
                    'device_name': self.__device_name,
                    'supplier': self.__supplier,
                    'app_receive': self.__app_receive,
                    'facility_receive': self.__facility_receive,
                    'token': self.__token,
                    'mode': self.__mode,
                }

                for sample in self.__samples:
                    exam_order = self.__exam_orders.get(sample['id'])

                    if exam_order is None:
                        message = self.__protocol.create_query_worklist(
                            **params_base,
                            datetime   = self.__protocol.format_date(datetime.now()),
                            message_id = self.generate_unique_identifier(),
                            sample_id  = sample['id'],
                            query_id   = self.generate_unique_identifier('Q'),
                            priority   = 'I'
                        ) 

                        sucess = self.__comunication.send_message(message)
                        max   = 3
                        count = 0
                        if sucess: 
                            for count in range(max):
                                if (exam_order := self.__exam_orders.get(sample['id'])):
                                    break
                                time.sleep(3)

                        if not exam_order:
                            responses.append(
                                f'Não foi possivel processar a amostra {sample["id"]}'
                            )
                            continue
                    
                    if exam_order:
                        patient = exam_order.get('patient') or {}

                        exam_orders = []

                        for order in exam_order.get('exam_orders', []):
                            observations = {}

                            necessary_observations = {
                                '00001': ['6690-2', '789-8', '718-7', '777-3']
                            }
    
                            exam_orders.append({
                                **order,
                                'observations': [
                                    observation
                                    for observation in sample['observations']
                                    if observation['code'] in necessary_observations.get(
                                        order.get('exam_id') or '', []
                                    )
                                ]
                            })

                        message = self.__protocol.create_result_exam(
                            **params_base,
                            datetime   = self.__protocol.format_date(datetime.now()),
                            message_id = self.generate_unique_identifier(),
                            patient_id = patient.get('id') or '',
                            paient_name = patient.get('name') or '',
                            patient_last_name = patient.get('last_name') or '',
                            patient_gender = patient.get('gender') or '',
                            patient_birth = patient.get('birth') or '',
                            alternative_patient_id = patient.get('alternative_id') or '',
                            visit_info = exam_order.get('visit_info') or None,
                            code_desc = code_desc,
                            exam_orders = exam_orders
                        )

                        sucess = self.__comunication.send_message(message)

                        if sucess:
                            responses.append(
                                f'Sample {sample["id"]} analyzed successfully'
                            )

                return responses
    
    def interpret(self, message: bytes):
        message_decode = self.__protocol.parser(message)

        if message_decode is None:
            return 'Error to parser message: Message invalid'

        message_decode_json = message_decode['json']
        headers = message_decode_json['headers']

        message_type = headers['message_type'] 

        message_strucuture = message_type.get('message_structure') or\
            f'{message_type.get("message_code")}_{message_type.get("trigger_event")}'
       
        match message_codes[self.__protocol.protocol_name].get(message_strucuture):
            case 'exam_orders':
                sample_id = message_decode_json["user_params"][0]
                match message_decode_json.get('query_result_status'):
                    case 'AE':
                        return 'Error in server to process sample '\
                                +f"{sample_id}'s exam orders"
                    case 'NF':
                        return f'The server did not find any '\
                            +f'exam order for sample {sample_id}'
                    case 'OK':
                        self.__exam_orders[sample_id] = {
                            'patient': message_decode_json.get('patients', [{}])[0],
                            'exam_orders': message_decode_json.get('exam_orders', [])
                        }
                        return f"Sample {sample_id}'s exam orders successfully processed"
        
        return message_decode

    @property
    def buffer_manager(self):
        return self.__protocol.buffer_manager
    
    @property
    def receive_message(self):
        return self.__comunication.receive_message

    def generate_unique_identifier(self, prefix = '') -> str:
        while True:
            identifier = prefix+str(randint(0, 9999)).zfill(4)

            if identifier not in self.__unique_identifiers:
                self.__unique_identifiers.append(identifier)
                return identifier

    def close(self):
        self.__comunication.close()
