import serial

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
    
    def receive_message(self) -> bytes:
        if self.__device is None: raise InterfaceNotStartedError()
        
        return self.__device.readline() 

    def send_message(self, message: bytes) -> bool:
        if self.__device is None: raise InterfaceNotStartedError()
        
        return self.__device.write(message) is not None

    def close(self): 
        if self.__device is not None:
            self.__device.close()
