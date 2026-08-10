import re

SEPARATORS = '|^~\\&'

VT = '\x0b'
FS = '\x1c'
CR = '\x0d'

VOID = ''

def get(list_: list, index: int, default = ''):
    return list_[index] if 0 <= index < len(list_) else default

class ProtocolHl7:
    def __init__(self, separators = SEPARATORS, version = '2.3.1') -> None:
        self.__separotors = separators
        self.__version    = version

    def create_message(self, *segments: str) -> bytes:
        return self.mllp(CR.join(segments)).encode()
    
    @property
    def field_separator(self) -> str:
        return self.__separotors[0]
    
    @property
    def component_separator(self) -> str:
        return self.__separotors[1]
    
    @property
    def repetition_separator(self) -> str:
        return self.__separotors[2]

    @property
    def subcomponent_separator(self) -> str:
        return self.__separotors[4] 

    @property
    def version(self):
        return self.__version

    def mult_void(self, n_voids: int):
        return [VOID]*n_voids

    def mllp(self, message: str) -> str:
        return f'{VT}{message}{FS}{CR}'

    def segment(self, segment_name: str, *fields: str) -> str:
        if segment_name == 'MSH' and (not fields[0] == self.__separotors):
            fields = (self.__separotors[1:], *fields)

        return self.field_separator.join([segment_name, *fields])

    def field(self, *components: str) -> str:
        return self.component_separator.join(components)

    def component(self, *subcomponents: str) -> str:
        return self.subcomponent_separator.join(subcomponents)

    def repetition(self, *fields: str) -> str:
        return self.repetition_separator.join(fields)

    def hl7_to_array(self, value_: str, re_sep, seps: list, level = 0):
        value = re.split(re_sep(seps[level]), value_)
        if len(value) == 1:
            value = value[0]

        next_level = level + 1

        if len(seps) == next_level:
            return value

        args = [re_sep, seps, next_level]

        return self.hl7_to_array(value, *args) if isinstance(value, str) else\
            [self.hl7_to_array(v, *args) for v in value]
 
    def parser(self, message_b: bytes):
        message: str = message_b.decode()

        START_BLOCK = message.index(VT)
        END_BLOCK   = message.index(f'{FS}{CR}')
        
        if START_BLOCK < 0 or END_BLOCK < 0:
            return None

        message  = message[START_BLOCK+1:END_BLOCK]
        segments = message.split(CR)

        msh = segments[0]

        if not msh.startswith('MSH'):
            return None

        field_separator        = msh[3]
        component_separator    = msh[4]
        repetition_separator   = msh[5]
        escape_char            = msh[6]
        subcomponent_separator = msh[7]

        re_sep = lambda sep: f"(?<!{escape_char}{escape_char}){escape_char}{sep}"

        headers: list[str]      = re.split(re_sep(field_separator), msh)
        message_type: list[str] = re.split(re_sep(component_separator), get(headers, 8))

        response: dict = {
            'headers': {
                'device_name'     : get(headers, 2),
                'supplier'        : get(headers, 3),
                'app_receive'     : get(headers, 4),
                'facility_receive': get(headers, 5),
                'datetime'        : get(headers, 6),
                'token'           : get(headers, 7),
                'message_type'    : {
                    'message_code'     : get(message_type, 0),
                    'trigger_event'    : get(message_type, 1),
                    'message_structure': get(message_type, 2)
                },
                'message_id': get(headers, 9),
                'mode': get(headers, 10),
                'version': get(headers, 11)
            }
        }

        for segment in segments:
            fieds = re.split(re_sep(field_separator), segment)
            match get(fieds, 0):
                case 'QPD':
                    query = re.split(re_sep(component_separator), get(fieds, 1))
                    response['equipment_standard_query'] = {
                        'identifier': get(query, 0),
                        'description': get(query, 1),
                        'coding_system': get(query, 2)
                    }
                    response['query_id']    = get(fieds, 2)
                    response['user_params'] = fieds[3:]

                case 'RCP':
                    response['query_priority'] = get(fieds, 1)
                    quantity_limited_request = re.split(
                        re_sep(component_separator),
                        get(fieds, 2)
                    )
                    response['quantity_limited_request'] = {
                        'quantity': get(quantity_limited_request, 0),
                        'unity': get(quantity_limited_request, 1)
                    }
                    response_sort_parameter = re.split(
                        re_sep(component_separator),
                        get(fieds, 3)
                    )
                    response['response_sort_parameter'] = {
                        'number_of_field': get(response_sort_parameter, 0),
                        'name_of_field': get(response_sort_parameter, 1)
                    }
                    response['modify_indicator'] = get(fieds, 4)
                    response['sort_order'] = get(fieds, 5)
                    response['segment_group_included'] = re.split(
                        re_sep(repetition_separator),
                        get(fieds, 6)
                    )

                    response['response_continuation_pointer'] = get(fieds, 7)

        return {
            'json' : response,
            'array': [
                self.hl7_to_array(segment, re_sep, [
                    field_separator,
                    repetition_separator,
                    component_separator,
                    subcomponent_separator
                ])
                for segment in segments
            ]
        }
