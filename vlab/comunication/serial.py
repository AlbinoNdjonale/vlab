import serial
from serial.tools import list_ports

class InterfaceNotStartedError(Exception):
    def __init__(self) -> None:
        super().__init__('Interface is not started')

class InterfaceSerial:
    def __init__(
        self,
        port: str,
        baudrate: int,
        bytesize: int,
        parity: str,
        stopbits: int
    ) -> None:
        self.__serial_port = port
        self.__baudrate    = baudrate
        self.__bytesize    = bytesize
        self.__parity      = parity
        self.__stopbits    = stopbits

        self.__device: serial.Serial|None = None

    def start_connection(self) -> None:
        self.__device = serial.Serial(
            self.__serial_port,
            baudrate = self.__baudrate,
            bytesize = self.__bytesize,
            parity   = self.__parity,
            stopbits = self.__stopbits
        )

    @property
    def get_conn(self):
        return None

    @property
    def get_bytes(self):
        return 1
    
    def receive_message(self) -> bytes:
        if self.__device is None: raise InterfaceNotStartedError()
        
        return self.__device.read(self.get_bytes)

    def send_message(self, message: bytes) -> bool:
        if self.__device is None: raise InterfaceNotStartedError()

        self.__device.write

        writed = self.__device.write(message)
        self.__device.flush()
        
        return writed is not None

    @property
    def id(self) -> str:
        for port in list_ports.comports():
            if port.device == self.__serial_port:
                if port.serial_number:
                    return port.serial_number

                return f'{port.vid}.{port.pid}.{port.location}'
        return self.__serial_port

    def close(self): 
        if self.__device is not None:
            self.__device.close()
