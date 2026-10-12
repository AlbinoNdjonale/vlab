from datetime import datetime
from typing import Callable, TypeAlias, Literal

from vlab.protocols import ProtocolHl7, VOID
from vlab.utils import ProtocolName

def is_number(number: str):
    try:
        float(number)
        return True
    except:
        return False

class Protocol:
    def __init__(self, protocol_name: ProtocolName) -> None:
        self.__protocol_name = protocol_name

        if protocol_name == 'HL7':
            self.__protocol = ProtocolHl7()
        elif protocol_name == 'ASTM':
            ...
        else:
            raise ValueError(f'Protocol not valid: {protocol_name}')

    def buffer_manager(
        self,
        receive: Callable[[], bytes]|None = None
    ):
        return self.__protocol.buffer_manager(receive)

    def create_ack(
        self,
        device_name: str,
        supplier: str,
        app_receive: str,
        facility_receive: str,
        datetime: str,
        mode: str,
        message_id: str,
        requisition_message_id: str,
        detail: str
    ):
        hl7 = self.__protocol

        return hl7.create_message(
            hl7.segment(
                'MSH', app_receive, facility_receive, device_name, supplier, datetime,
                VOID, hl7.field('ACK', 'R01', 'RSP_K21'), message_id, mode, hl7.version
            ),
            hl7.segment('MSA', 'AA', requisition_message_id, detail)
        )

    def create_query_worklist(
        self,
        device_name: str,
        supplier: str,
        app_receive: str,
        facility_receive: str,
        datetime: str,
        token: str,
        mode: str,
        sample_id: str,
        query_id: str,
        message_id: str,
        priority: str
    ) -> bytes:
        hl7 = self.__protocol

        return hl7.create_message(
            hl7.segment(
                'MSH', device_name, supplier, app_receive, facility_receive, datetime,
                VOID, hl7.field('QBP', 'Q21', 'QBP_Q21'), message_id, mode, hl7.version
            ),
            hl7.segment('QPD', hl7.field('Q11', 'Query', 'HL7'), query_id, sample_id),
            hl7.segment('RCP', priority)
        )

    def create_lote_order_exam(
        self,
        device_name: str,
        supplier: str,
        app_receive: str,
        facility_receive: str,
        datetime: str,
        mode: str,
        message_id: str,
        patients: list = [],
    ):
        hl7 = self.__protocol

        return hl7.create_message(
            hl7.segment(
                'MSH', app_receive, facility_receive, device_name, supplier, datetime,
                VOID, hl7.field('ORM', 'O01', 'RSP_K21'), message_id, mode, hl7.version
            ),
            *[
                segment
                for group in
                (
                    [
                        hl7.segment(
                            'PID', str(idx+1), VOID, patient.get('id') or VOID,
                            patient.get('alternative_id') or VOID,
                            hl7.field(
                                patient.get('name') or VOID,
                                patient.get('last_name') or VOID
                            ),
                            VOID, patient.get('birth') or VOID,
                            patient.get('gender') or VOID
                        ),
                        hl7.segment(
                            'ORC', patient.get('order_code') or VOID,

                        )
                    ]
                    for idx, patient in enumerate(patients)
                )
                for segment in group
            ]
        )

    def create_order_exam(
        self,
        device_name: str,
        supplier: str,
        app_receive: str,
        facility_receive: str,
        datetime: str,
        mode: str,
        message_id: str,
        message_processing_status: str,
        requisition_message_id: str,
        query_result_status: str,
        requisition_query_id: str,
        sample_id: str = '',
        esq_id: str = '',
        esq_description: str = '',
        esq_codibg_system: str = '',
        patient_id: str = '',
        paient_name: str = '',
        patient_last_name: str = '',
        patient_birth: str = '',
        patient_gender: str = '',
        exam_orders: list = [],
        table_coding: dict[str, str] = {},
        exam_sytem: dict = {},
        alternative_patient_id: str = '',
        visit_info: dict|None = None
    ):
        hl7 = self.__protocol

        return hl7.create_message(
            hl7.segment(
                'MSH', app_receive, facility_receive, device_name, supplier, datetime,
                VOID, hl7.field('RSP', 'K21', 'RSP_K21'), message_id, mode, hl7.version
            ),
            hl7.segment('MSA', message_processing_status, requisition_message_id),
            hl7.segment('QAK', requisition_query_id, query_result_status),
            hl7.segment(
                'QPD', hl7.field(esq_id, esq_description, esq_codibg_system),
                requisition_query_id, sample_id
            ),
            hl7.segment(
                'PID', '1', VOID, patient_id, alternative_patient_id, hl7.field(
                    paient_name,
                    patient_last_name
                ),
                VOID, patient_birth, patient_gender
            ) if patient_id else '',
            hl7.segment(
                'PV1', '1', visit_info.get('patient_class') or VOID,
                hl7.field(
                    visit_info.get('point_care') or VOID,
                    visit_info.get('room') or VOID,
                    visit_info.get('bed') or VOID
                ), *([VOID]*3),
                visit_info.get('attending_doctor') or VOID,
                *([VOID]*11),
                visit_info.get('id') or VOID
            ) if visit_info else '',
            *[
                hl7.segment(
                    'OBR', str(idx+1), VOID,
                    exam_order.get('sample_id') or VOID,
                    hl7.field(
                        exam_sytem.get(exam_order.get('exam_id') or VOID) or VOID,
                        exam_order.get('exam_description') or VOID,
                        table_coding.get(exam_order.get('exam_id') or VOID) or VOID
                    ),
                    *([VOID]*20),
                    exam_order.get('exam_result_status') or VOID
                )
                for idx, exam_order in enumerate(exam_orders)
            ]
        )

    def create_result_exam(
        self,
        device_name: str,
        supplier: str,
        app_receive: str,
        facility_receive: str,
        datetime: str,
        token: str,
        mode: str,
        message_id: str,
        patient_id: str = '',
        paient_name: str = '',
        patient_last_name: str = '',
        patient_birth: str = '',
        patient_gender: str = '',
        alternative_patient_id: str = '',
        visit_info: dict|None = None,
        exam_orders: list[dict] = [],
        code_desc: dict[str, str] = {}
    ):
        hl7 = self.__protocol

        per = lambda de, nu: (de/nu)*100

        return hl7.create_message(
            hl7.segment(
                'MSH', device_name, supplier, app_receive, facility_receive, datetime,
                VOID, hl7.field('ORU', 'R01'), message_id, mode, hl7.version
            ),
            hl7.segment(
                'PID', '1', VOID, patient_id, alternative_patient_id, hl7.field(
                    paient_name,
                    patient_last_name
                ),
                VOID, patient_birth, patient_gender
            ),
            hl7.segment(
                'PV1', '1', visit_info.get('patient_class') or VOID,
                hl7.field(
                    visit_info.get('point_care') or VOID,
                    visit_info.get('room') or VOID,
                    visit_info.get('bed') or VOID
                ), *([VOID]*3),
                visit_info.get('attending_doctor') or VOID,
                *([VOID]*11),
                visit_info.get('id') or VOID
            ) if visit_info else '',
            *[
                segment
                for group in
                (
                    [ 
                        hl7.segment(
                            'OBR', str(idx+1), exam_order.get('id') or VOID,
                            exam_order.get('executor_side_id') or VOID,
                            hl7.field(
                                exam_order.get('exam_id') or VOID or VOID,
                                exam_order.get('exam_description') or VOID,
                                exam_order.get('table_coding') or VOID or VOID
                            ),
                            VOID, VOID, datetime, *([VOID]*17), 'F'
                        ),
                        *[
                            hl7.segment(
                                'OBX', str(idx_+1), obs.get('type_value') or VOID,
                                hl7.field(
                                    obs.get('code') or VOID,
                                    code_desc.get(obs.get('code') or VOID) or VOID,
                                    'LN'
                                ), VOID, obs.get('value') or VOID,
                                (obs.get('unity') or VOID).replace('^', r'\^'),
                                f"{obs.get('ref_min') or VOID}-{obs.get('ref_max') or VOID}",
                                (
                                    'LL' if per(
                                        float(obs.get('ref_min')) - float(obs.get('value')),
                                        float(obs.get('ref_min'))
                                ) > 50 else (
                                    'L' if per(
                                        float(obs.get('ref_min')) - float(obs.get('value')),
                                        float(obs.get('ref_min'))
                                ) > 0 else (
                                    'HH' if per(
                                        float(obs.get('value')) - float(obs.get('ref_max')),
                                        float(obs.get('ref_max'))
                                ) > 50 else (
                                    'H' if per(
                                        float(obs.get('value')) - float(obs.get('ref_max')),
                                        float(obs.get('ref_max'))
                                ) > 0 else 'N'
                                )))) if (
                                    is_number(obs.get('value')) and
                                    is_number(obs.get('ref_min')) and
                                    is_number(obs.get('ref_max'))
                                ) else VOID, obs.get('probability') or VOID, VOID,
                                'F'
                            )
                            for idx_, obs in enumerate(exam_order.get('observations', {}))
                        ]
                    ]
                    for idx, exam_order in enumerate(exam_orders)
                )
                for segment in group
            ] 
        )

    def parser(self, mesage: bytes):
        return self.__protocol.parser(mesage)

    @property
    def protocol_name(self):
        return self.__protocol_name

    def format_date(self, date: datetime) -> str:
        return date.strftime('%Y%m%d%H%M%S')
