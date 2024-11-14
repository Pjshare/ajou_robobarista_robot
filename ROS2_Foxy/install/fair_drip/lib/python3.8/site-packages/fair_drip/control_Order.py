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

# async def update_drip_f(pos):
#     conn = await Access()
    
#     async with conn.cursor() as cursor:
#         DATA = await DBset_Load()    
#         DT = DATA['DB']['STATETABLE']
#         if pos == 1:
#             Update_Q = f"UPDATE {DT} SET drip_state = '완료' WHERE drip_point = 'DripHole_1'"
#         elif pos == 2:
#             Update_Q = f"UPDATE {DT} SET drip_state = '완료' WHERE drip_point = 'DripHole_2'"
#         elif pos == 3:
#             Update_Q = f"UPDATE {DT} SET drip_state = '완료' WHERE drip_point = 'DripHole_3'"
#         await cursor.execute(Update_Q)
#         await conn.commit()

#     conn.close()


# async def update_drip_f2(pos):
#     conn = await Access()
    
#     async with conn.cursor() as cursor:
#         DATA = await DBset_Load()    
#         DT = DATA['DB']['STATETABLE']
#         if pos == 1:
#             Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE drip_point = 'DripHole_1'"
#         elif pos == 2:
#             Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE drip_point = 'DripHole_2'"
#         elif pos == 3:
#             Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE drip_point = 'DripHole_3'"
#         await cursor.execute(Update_Q)
#         await conn.commit()

#     conn.close()

# async def update_drip_point_f(pos):
#     pos = int(pos)
#     conn = await Access()

#     async with conn.cursor() as cursor:
#         DATA = await DBset_Load()    
#         DT = DATA['DB']['STATETABLE']

#         Update_Q = f"UPDATE {DT} SET drip_state = '준비대기' WHERE No = '{int(pos)}'"
        
#         await cursor.execute(Update_Q)
#         await conn.commit()

#      conn.close()

##DB 수정 필요 
# async def update_drip_point(pos): 
#     conn = await Access()

#     async with conn.cursor() as cursor:
#         DATA = await DBset_Load()    
#         DT = DATA['DB']['STATETABLE']

#         Update_Q = f"UPDATE {DT} SET drip_state = '없음' WHERE No = '{pos}'"
       
#         await cursor.execute(Update_Q)
#         await conn.commit()

#     conn.close()

async def check_drip_point(dripper_data):
    # 사용 가능한 드리퍼 중 가장 낮은 order를 찾기 위한 초기값
    selected_point = None
    print("CONTROL_ORDER")
    print("DRIP+POINT")

    
    for dripper in dripper_data:
        # 조건을 만족하는 드리퍼 찾기
        if dripper['exist_dripper'] is True and dripper['exist_coffee_beans'] is True:
            # 첫 번째로 조건을 만족하는 드리퍼거나, 현재 선택된 order보다 낮으면 업데이트
            if selected_point is None or dripper['order'] < selected_point:
                selected_point = dripper['order']

    print("Select Point"+selected_point)
    return selected_point


async def check_cup_point(cup_data):
    # 사용 가능한 컵 중 가장 낮은 order를 찾기 위한 초기값
    print("CONTROL_ORDER")
    print("CUP+POINT")
    selected_point = None

    for cup in cup_data:
        # exist_cup이 False인 (비어 있지 않은) 컵을 찾기
        if cup['exist_cup'] is True:
            # 첫 번째로 조건을 만족하는 컵이거나, 현재 선택된 order보다 낮으면 업데이트
            if selected_point is None or cup['order'] < selected_point:
                selected_point = cup['order']
    print("Select Point"+selected_point)
    return selected_point

