from abc import ABC, abstractmethod
import json
from typing import cast
import os

class BaseModel(ABC):
    __path__: str = './vlab/agent/infrastructure/entity/'
    
    __filename__: str|None = None
    __fields__: list[str]|None = None

    __abstractatrributes__: list[str] = ['__filename__', '__fields__']

    def __init__(self) -> None:
        for attribute in BaseModel.__abstractatrributes__:
            if getattr(self, attribute) is None:
                raise TypeError(
                    'Can not instantiate abstract '\
                    +f'class with abstract atribute {attribute}'
                )

        if not os.path.exists(self.filename):
            with open(self.filename, 'w'): ...
        else:
            with open(self.filename, 'r') as file:
                data = json.loads(file.read())

                for key in cast(list[str], self.__fields__):
                    if key in data:
                        setattr(self, key, data[key])
                            
    def save(self):
        data = {
            key: getattr(self, key)
            for key in cast(list[str], self.__fields__)
        }

        with open(self.filename, 'w') as file:
            file.write(json.dumps(data))

    @property
    def filename(self) -> str:
        return f'{self.__path__}{self.__filename__}'
