import json
import os
from typing import cast, Required, TypeAlias, TypedDict, Literal

Infinit: TypeAlias = Literal['Infinit']

ProtocolName: TypeAlias = Literal['HL7', 'ASTM']

class Config(TypedDict, total = False):
    SERIAL_MODE: Required[bool]
    PROTOCOL: Required[ProtocolName]

    APPARATUS_SERIAL_PORT: Required[str]
    BAUDRATE: int
    BYTESIZE: int
    PARITY: str
    STOPBITS: int

    AGENT_TCP_PORT: Required[int]
    APPARATUS_TCP_PORT: Required[int]
    TCP_HOST: str
    GATEWAY_MAX_CLIENT: Required[int|Infinit]
    APPARATUS_AS_SERVER: Required[bool]

    MODE: Literal['P', 'T', 'D']

START_COMMENT = '#'

class Utils:
    @staticmethod
    def read_config(file_config = './vlab.config') -> Config:
        if os.path.exists(file_config):
            with open(file_config, 'r') as file:
                configs = {}
                for line in file.read().split('\n'):
                    line_striped = line.strip()

                    if line_striped == '' or line_striped[0] == START_COMMENT:
                        continue

                    content_main = line_striped.split(START_COMMENT, 1)[0].strip()
                    
                    key, value = content_main.split('=', 1)
                    
                    configs[key.strip()] = Utils.parse(value.strip())
            
            return cast(Config, configs)
        else:
            return cast(Config, {})

    @staticmethod
    def parse(value: str) -> str:
        values = {
            'true': True,
            'false': False,
            'null': None,
            'none': None,
            'infinit': 'Infinit'
        }

        if value.lower() in values: return values[value.lower()]

        return json.loads(value)

    @staticmethod
    def take_numbres(number: int|Infinit):
        count = 0
        
        while True:
            yield count

            count += 1

            if not number == 'Infinit' and number <= count:
                break
