import serial
import serial.tools.list_ports
import time
import logging
import asyncio

import re

async def extract_temperature_values(response):
    match = await re.search(r'\+TEMP:(\d+),\s*(\d+)', str(response))
    if match:
        temp1 = match.group(1)
        temp2 = match.group(2)
        return int(temp1), int(temp2)
    else:
        raise ValueError("형식이 올바르지 않습니다.")

# SERIAL_PORT = 'COM3' # 윈도우
SERIAL_PORT = '/dev/ttyUSB0' # 우분투
BAUD_RATE = 9600

logger = logging.getLogger(__name__)

async def send_at_command(command):
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        await ser.write((command + '\r\n').encode())
        await asyncio.sleep(0.5)  
        response = await ser.read_all().decode()
        return response

async def set_target_temperature(temp):
    response = await send_at_command(f'AT+TEMP={temp}')
    return response

async def query_temperature(): 
    response = await send_at_command('AT+TEMP?')
    temp1, temp2 = parse_temperature(response)
    return temp1, temp2

async def setup_parameters(index, temperature, volume):
    response = await send_at_command(f'AT+SETUP={index},{temperature},{volume}')
    return response

async def trigger_output(setting):  
    response = await send_at_command(f'AT+OUTPUT={setting}')
    return response

async def parse_temperature(response):
    try:
        if response.startswith('+TEMP:'):
            return extract_temperature_values(response)
        else:
            raise ValueError("형식이 올바르지 않습니다.")
    except ValueError as e:
        logger.error(f"온도 파싱 오류: {e}")
        return None, None