import serial
import serial.tools.list_ports
import logging
import asyncio

logger = logging.getLogger(__name__)

SERIAL_PORT = '/dev/ttyUSB1' # 우분투

def cup_out():
    try:
        with serial.Serial(port=SERIAL_PORT, baudrate=115200, timeout=1) as port:
            logger.info(f'Connected to {SERIAL_PORT}')
            working_count = 0
            fin_count = 0
            buf = bytearray([0x04, 0x07, 0xAA, 0x01, 0x00, 0xB6, 0xFF])
            ############### 명령 + 길이 + 명령 + 데이터 + 데이터N + 체크섬 + 종료
            check_buf = bytearray([0x01, 0x05, 0x55, 0x5B, 0xFF])
            
            port.write(check_buf)
            while True:
                if port.in_waiting > 0:
                    data = port.read(port.in_waiting)
                    comp_buffer = bytearray([0x01])
                    fin_buffer = bytearray([0x00])
                    error_buffer = bytearray([0x02])
                    
                    logger.info(f'Received data:1 {data}')
                    break
            msg = '출력'
            return msg
           
    except Exception as e:
        logger.error(f"Error: {e}")
