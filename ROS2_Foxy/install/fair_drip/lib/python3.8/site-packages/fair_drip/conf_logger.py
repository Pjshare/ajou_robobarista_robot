import logging
import os

C_FILE_PATH = os.path.abspath(__file__)
C_FILEDIR_PATH = os.path.dirname(C_FILE_PATH)

log_file_path = os.path.join(C_FILEDIR_PATH, 'drip_action.log') 

def connect(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)  

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.info('App Connected')

def action(name, msg):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)  

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.info(f'Drip_Robot Moving : {msg}')  

def error(name, msg):
    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)  

    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.ERROR)  

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.error(f'Drip_Robot Error : {msg}')  