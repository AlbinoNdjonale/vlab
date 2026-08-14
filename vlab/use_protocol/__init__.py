from datetime import datetime
from typing import TypeAlias, Literal

from vlab.protocols import ProtocolHl7, VOID
from vlab.utils import ProtocolName

class Protocol:
    def __init__(self, protocol_name: ProtocolName) -> None:
        self.__protocol_name = protocol_name

        if protocol_name == 'HL7':
            self.__protocol = ProtocolHl7()
        elif protocol_name == 'ASTM':
            ...
        else:
            raise ValueError(f'Protocol not valid: {protocol_name}')

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

    def create_order_exame(
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
        exame_orders: list = [],
        table_coding: dict[str, str] = {},
        exam_sytem: dict = {},
        alternative_patient_id: str = ''
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
            *[
                hl7.segment(
                    'OBR',
                    str(idx+1),
                    exam_order.get('id') or VOID,
                    exam_order.get('executor_side_id') or VOID,
                    hl7.field(
                        exam_sytem.get(exam_order.get('exam_id') or VOID) or VOID,
                        exam_order.get('exam_description') or VOID,
                        table_coding.get(exam_order.get('exam_id') or VOID) or VOID
                    ),
                    *(['']*20),
                    exam_order.get('exam_result_status') or VOID
                )
                for idx, exam_order in enumerate(exame_orders)
            ]
        )

    def parser(self, mesage: bytes):
        return self.__protocol.parser(mesage)

    def format_date(self, date: datetime) -> str:
        return date.strftime('%Y%m%d%H%M%S')
