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

    def __init__(self, config_file: str) -> None:
        self.__config_file = config_file

        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                data = json.loads(file.read())

                for key in self.__fields__:
                    if key in data:
                        setattr(self, key, data[key])

    @property
    def filename(self):
        return f'{self.__path__}{self.__config_file}'
