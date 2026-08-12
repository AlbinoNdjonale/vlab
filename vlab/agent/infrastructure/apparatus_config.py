import json
import os
from typing import TypeAlias, Literal

MessageCode: TypeAlias = Literal['query_exam_orders']

class ApparatusConfig:
    __path__: str = './vlab/agent/infrastructure/apparatus_configs/'

    __fields__ = ['message_codes']

    message_codes: dict[str, MessageCode] = {}
    exame_system: dict[str, str] = {}
    table_coding: dict[str, str] = {}

    def __init__(self, config_file: str, address: str) -> None:
        self.__config_file = config_file
        self.__address = address

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
