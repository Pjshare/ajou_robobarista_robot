# -*- coding: UTF-8 -*-

import pymysql
import time
import yaml, os
import asyncio
import aiomysql

C_FILE_PATH = os.path.abspath(__file__)
C_FILEDIR_PATH = os.path.dirname(C_FILE_PATH)

YAML_PATH = os.path.join(C_FILEDIR_PATH, "Set_Value.yaml")

def time_check():
    now = time.localtime()
    f_now = time.strftime("%Y-%m-%d %H:%M:%S", now)

    return f_now

async def DBset_Load():
    with open(YAML_PATH, 'r') as file:
        data = yaml.safe_load(file)
        
    return data

async def Access():
    DATA = await DBset_Load()
    DID = DATA['DB']['DB_ID']
    DPW = DATA['DB']['DB_PW']
    DIP = DATA['DB']['DB_IP']
    DPO = DATA['DB']['PORT']
    DB = DATA['DB']['DATABASE']

    conn = await aiomysql.connect(host=DIP, user=DID, password=DPW, port=int(DPO), db=DB, charset='utf8', connect_timeout=2)
    return conn

async def order_insert(name, info):
    state = '대기'
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['ORDERTABLE']
        today_start = time.strftime('%Y-%m-%d') + ' 00:00:00'
        today_end = time.strftime('%Y-%m-%d') + ' 23:59:59'
        Check_Q = f'SELECT MAX(order_no) FROM {DT} WHERE order_date BETWEEN "{today_start}" AND "{today_end}"'
        
        await cursor.execute(Check_Q)
        Check_No = await cursor.fetchall()

        No = 1 if Check_No[0][0] is None else Check_No[0][0] + 1

        Time_log = time_check()
        Insert_Q = f"INSERT INTO {DT} (order_no, order_date, recipe_name, recipe_state, recipe_info) VALUES ('{No}', '{Time_log}', '{name}', '{state}', '{info}')"
        
        await cursor.execute(Insert_Q)
        await conn.commit()

    conn.close()
    return (No, Time_log)

async def order_update_m(No, Time_log, Order_Pos):
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['ORDERTABLE']

        Update_Q = f"UPDATE {DT} SET recipe_state = '진행중', order_position = '{int(Order_Pos)}' WHERE order_no = '{int(No)}' AND order_date = '{Time_log}'"
        
        await cursor.execute(Update_Q)
        await conn.commit()
    print("진행중 업데이트")
    conn.close()

async def order_update_f(No, S_Time_log):
    Time_log = time_check()
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['ORDERTABLE']

        Update_Q = f"UPDATE {DT} SET recipe_state = '완료', order_finish_date = '{Time_log}' WHERE order_no = '{int(No)}' AND order_date = '{S_Time_log}'"
        print(Update_Q)
        await cursor.execute(Update_Q)
        await conn.commit()

    conn.close()

async def update_drip_f(pos):
    conn = await Access()
    
    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['STATETABLE']
        if pos == 1:
            Update_Q = f"UPDATE {DT} SET drip_state = '완료' WHERE drip_point = 'DripHole_1'"
        elif pos == 2:
            Update_Q = f"UPDATE {DT} SET drip_state = '완료' WHERE drip_point = 'DripHole_2'"
        elif pos == 3:
            Update_Q = f"UPDATE {DT} SET drip_state = '완료' WHERE drip_point = 'DripHole_3'"
        await cursor.execute(Update_Q)
        await conn.commit()

    conn.close()


async def update_drip_f2(pos):
    conn = await Access()
    
    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['STATETABLE']
        if pos == 1:
            Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE drip_point = 'DripHole_1'"
        elif pos == 2:
            Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE drip_point = 'DripHole_2'"
        elif pos == 3:
            Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE drip_point = 'DripHole_3'"
        await cursor.execute(Update_Q)
        await conn.commit()

    conn.close()

async def update_drip_point_f(pos):
    pos = int(pos)
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['STATETABLE']

        Update_Q = f"UPDATE {DT} SET drip_state = '준비대기' WHERE No = '{int(pos)}'"
        
        await cursor.execute(Update_Q)
        await conn.commit()

    conn.close()

async def update_drip_point(pos):
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['STATETABLE']

        Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE No = '{pos}'"
       
        await cursor.execute(Update_Q)
        await conn.commit()

    conn.close()

async def check_drip_point():
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['STATETABLE']

        Update_Q = f"SELECT drip_state FROM {DT} WHERE drip_point IN ('DripHole_1', 'DripHole_2', 'DripHole_3')"
        await cursor.execute(Update_Q)

        check_point = await cursor.fetchall()

        selected_point = None
        if check_point[0][0] == '없음':
            selected_point = 1
        elif check_point[1][0] == '없음':
            selected_point = 2
        elif check_point[2][0] == '없음':
            selected_point = 3
        else:
            selected_point = 1
    conn.close()
    return selected_point

async def check_drip_select():
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['STATETABLE']

        Update_Q = f"SELECT drip_state FROM {DT} WHERE drip_point IN ('1층_1', '1층_2', '1층_3', '2층_1', '2층_2', '2층_3', '3층_1', '3층_2', '3층_3')"
        await cursor.execute(Update_Q)

        check_point = await cursor.fetchall()

        selected_point = None
        for idx, state in enumerate(check_point):
            if state[0] == '준비완료':
                selected_point = idx + 1
                break

    conn.close()
    return selected_point

async def check_dripback_select():
    conn = await Access()

    async with conn.cursor() as cursor:
        DATA = await DBset_Load()    
        DT = DATA['DB']['STATETABLE']

        Update_Q = f"SELECT drip_state FROM {DT} WHERE drip_point IN ('1층_1', '1층_2', '1층_3', '2층_1', '2층_2', '2층_3', '3층_1', '3층_2', '3층_3')"
        await cursor.execute(Update_Q)

        check_point = await cursor.fetchall()

        selected_point = None
        for idx, state in enumerate(check_point):
            if state[0] == '없음':
                selected_point = idx + 1
                break

    conn.close()
    return selected_point
