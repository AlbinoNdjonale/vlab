import json
import os
from typing import cast, TypeAlias, Literal

MessageCode: TypeAlias = Literal['query_exam_orders']

Protocol: TypeAlias = Literal['HL7', 'ASTM']

class ApparatusConfig:
    __path__: str = './vlab/agent/infrastructure/apparatus_configs/'
    __pathaddress__: str = f'{__path__}address/'

    __fields__ = ['message_codes', 'exame_system', 'table_coding']

    __protocol: Protocol|None = None

    message_codes: dict[str, MessageCode] = {}
    exame_system: dict[str, str] = {}
    table_coding: dict[str, str] = {}

    def __init__(self, address: str) -> None:
        self.__address = address

        file_protocol = f'{ApparatusConfig.__pathaddress__}{address}'
        if os.path.exists(file_protocol):
            with open(file_protocol, 'r') as file:
                self.__protocol = cast(Protocol, file.read())

            if os.path.exists(self.filename_default):
                self.read_contract(self.filename_default)

    def set_apparatus(self, config_file: str):
        self.__config_file = config_file

        if os.path.exists(self.filename):
            self.read_contract(self.filename) 
        elif os.path.exists(self.filename_tmp):
            self.read_contract(self.filename_tmp)
            os.rename(self.filename_tmp, self.filename)

    def read_contract(self, filename: str):
        with open(filename, 'r') as file:
            data = json.loads(file.read())

            for key in self.__fields__:
                if key in data:
                    setattr(self, key, data[key])

    @property
    def filename(self):
        return f'{self.__path__}{self.__config_file}'

    @property
    def filename_tmp(self):
        return f'{self.__path__}{self.__address}'
    
    @property
    def filename_default(self):
        return f'{self.__path__}DEFAULT_{self.__protocol}'
    
    @property
    def protocol(self):
        return self.__protocol

    @staticmethod
    def create_config(filenname: str, content: dict):
        with open(f'{ApparatusConfig.__path__}{filenname}', 'w') as file:
            file.write(json.dumps(content))

    @staticmethod
    def set_protocol(protocol: Protocol, device_address: str):
        with open(f'{ApparatusConfig.__pathaddress__}{device_address}', 'w') as file:
            file.write(protocol)
