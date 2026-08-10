from datetime import datetime
from typing import TypeAlias, Literal

from vlab.protocols import ProtocolHl7, VOID
from vlab.utils import ProtocolName

class Protocol:
    def __init__(self, protocol_name: ProtocolName) -> None:
        self.__protocol_name = protocol_name

        if protocol_name == 'HL7':
            self.__protocol = ProtocolHl7()
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

        return self.__protocol.create_message(
            hl7.segment(
                'MSH', device_name, supplier, app_receive, facility_receive, datetime,
                VOID, hl7.field('QBP', 'Q21', 'QBP_Q21'), message_id, mode, hl7.version
            ),
            hl7.segment('QPD', hl7.field('Q11', 'Query', 'HL7'), query_id, sample_id),
            hl7.segment('RCP', priority)
        )

    def parser(self, mesage: bytes):
        return self.__protocol.parser(mesage)

    def format_date(self, date: datetime) -> str:
        return date.strftime('%Y%m%d%H%M%S')
