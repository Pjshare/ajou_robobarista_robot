"#-*- coding: UTF-8 -*-"
import sys
sys.path.append('~/ros_ws/src/Ajou_Drip_Project-main/ROS2_Foxy')
import asyncio
import websockets # type: ignore
import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import os, sys

C_FILE_PATH = os.path.abspath(__file__)
C_FILEDIR_PATH = os.path.dirname(C_FILE_PATH)
sys.path.append(C_FILEDIR_PATH)

import frrpc

import fair_drip.conf_file as cf
import fair_drip.control_v2 as rc
import fair_drip.control_Temp_M  as tm
import fair_drip.control_Cup_Dis  as cd
import fair_drip.control_Order  as Or

import re
## Robot info
ROBOT_IP = "192.168.58.2"
robot = frrpc.RPC(ROBOT_IP)

EP=[0.000, 0.000, 0.000, 0.000]
DP=[1.000, 1.000, 1.000, 1.000, 1.000, 1.000]
EP2=[0.000,0.000,0.000,0.000]

TOTAL_STEP = 13

class Listener(Node):
    def __init__(self):
        super().__init__('listener')
        self.publisher = self.create_publisher(String, '/robot', 10)
        ### sub
        self.sub_check = self.create_subscription(
            String, 'pos', self.listener_callback, 10)
        self.sub_check
        self.subscription = self.create_subscription(
            String, 'drip', self.listener_callback, 10)
        self.subscription

        self.lock = asyncio.Lock()  
        
        self.websocket_uri = "ws://192.168.58.8:9090"
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:  
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.connect_websocket())

    async def connect_websocket(self):
        self.websocket = await websockets.connect(self.websocket_uri)
        if self.websocket.open:
            self.get_logger().info('WebSocket connected successfully')
    
    async def listener_callback(self, msg):
        async with self.lock:  
            data = msg['data'].strip()
            data = data.replace("'", '"')
            data = json.loads(data)
            print(type(data))
            sub_msg1 = data.get('conn')
            sub_msg2 = data.get('pos')

            msg_Coffee = data['recipe'].get('coffee')
            msg_Type = data['recipe'].get('drip_type')
            msg_Temp = data['recipe'].get('water_temp')
            msg_WTotal = data['recipe'].get('water_total')
            msg_WM = data['recipe'].get('water_method')
            msg_TM = data['recipe'].get('time_method')

            recipe_w = msg_WM.split(', ') if msg_WM else []
            recipe_t = msg_TM.split(', ') if msg_TM else []
            self.get_logger().info(f"Received raw data: {data}")
            if None in [msg_Coffee]: 
                
                if sub_msg1:
                    self.publish_msg_check(sub_msg1)
                elif sub_msg2:
                    await self.drip_clearing(sub_msg2)
            else:
                print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
                await rc.SetSpeed(10)
                await rc.set_home()
                await self.recipe_dripper(msg_Coffee, msg_Type, msg_Temp, msg_WTotal, msg_WM, len(recipe_w), msg_TM, len(recipe_t))
            
    async def recipe_dripper(self, coffee, type, temp, wtotal, wm, wmc, tm, tmc):
        coffee_count = int(coffee)/2
        current_step = 0
        self.progress_info(current_step)

        order_set1, order_set2, order_set3, order_set4 = await asyncio.gather(
            Or.order_insert(coffee, str(wm)),
            self.temp_S(temp),
            Or.check_drip_point(),
            Or.check_drip_select()
        )
        current_step = 4
        self.progress_info(current_step)

        if order_set3 == None:
            msg = '진행대기'
            self.publish_msg_robot(msg)

        else:
            await Or.order_update_m(order_set1[0], order_set1[1], order_set3)
            await self.drip_set_move(order_set3, order_set4)
            await Or.update_drip_point(order_set4)
            current_step = 9
            self.progress_info(current_step)
            if order_set3 is None:
                print("준비상태 확인 ")
            else:
                await self.coffee_drop(order_set3, coffee_count)
                current_step = 16
                self.progress_info(current_step)

                await self.cup_set_move(order_set3)
                current_step = 19
                self.progress_info(current_step)

                await self.water_move(order_set2, temp)
                current_step = 22
                self.progress_info(current_step)

                await self.drip_water(order_set3, type, wm, wmc, tm, tmc)
                current_step = 26
                self.progress_info(current_step)

                current_step = 29
                self.progress_info(current_step)

                await rc.set_home()
                current_step = 30
                self.progress_info(current_step)
                await Or.order_update_f(order_set1[0], order_set1[1])
                print("finish")
                await Or.update_drip_f(order_set3)
                current_step = 31
                self.progress_info(current_step)

    def progress_info(self, step):
        pr = (step/TOTAL_STEP)*100

        self.publish_msg_robot(pr)
    
    def publish_msg_robot(self, msg):
        message_data = {
            "op": "publish",  
            "topic": "/robot", 
            "msg": {
                "data": str(msg)
            }
        }
        message_json = json.dumps(message_data)  

        asyncio.run_coroutine_threadsafe(self.send_websocket_message(message_json), self.loop)
    
    def publish_msg_check(self, msg):
        message_data = {
            "op": "publish", 
            "topic": "/check",  
            "msg": {
                "data": "0"
            }
        }
        message_json = json.dumps(message_data)  

        asyncio.run_coroutine_threadsafe(self.send_websocket_message(message_json), self.loop)
    
    def time_check():
        now = time.localtime()
        f_now = time.strftime("%H:%M:%S", now)

        return f_now

    async def send_websocket_message(self, message):
        if self.websocket.open:
            await self.websocket.send(message)  
            self.get_logger().info(f'Published to WebSocket: {message}')

    async def temp_S(self, temp):
        try:
            response = await tm.async_send_at_command(f'AT+TEMP={temp}')
            await tm.set_target_temperature(temp)
            await tm.setup_parameters(1, temp, 430)

            temp_res = await tm.query_temperature()
            print(temp_res)
            match = re.search(r'\+TEMP:(\d+),\s*(\d+)', str(temp_res))
            if match:
                temp1 = match.group(1)
                temp2 = match.group(2)
                if abs(int(temp1) - int(temp2)) <= 1:                
                    check_msg = 'ok'
                    return check_msg
                
                else:                
                    check_msg = 'ng'
                    return check_msg
        except:
            self.get_logger().info('Temp_Set Run Error')
    
            pass
    async def temp_M(self):
        try:
            temp_res = await tm.query_temperature()
            match = re.search(r'\+TEMP:(\d+),\s*(\d+)', str(temp_res))
            if match:     
                temp1 = match.group(1)
                temp2 = match.group(2)    
                if abs(int(temp1) - int(temp2)) <= 1:                
                    check_msg = 'ok'
                    return check_msg  
                
        except:
            self.get_logger().info('Temp_Move Run Error')
    
            
            check_msg = 'ok'
            return check_msg
            
    async def drip_set_move(self, drip_point, drip_select): # drip 위치
        if drip_select == 1:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper1()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper1()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper1()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_3rd_pos()

        elif drip_select == 2:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper2()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper2()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper2()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_3rd_pos()
            
        elif drip_select == 3:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper3()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper3()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper3()
                await rc.new_ready_for_set_1st_floor_dripper()
                await rc.new_set_dripper_3rd_pos()
            
        elif drip_select == 4:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper4()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper4()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper4()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_3rd_pos()
            
        elif drip_select == 5:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper5()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper5()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper5()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_3rd_pos()
            
        elif drip_select == 6:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper6()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper6()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper6()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_3rd_pos()
            
        elif drip_select == 7:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper7()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper7()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper7()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_3rd_pos()
            
        elif drip_select == 8:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper8()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper8()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper8()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_3rd_pos()
            
        elif drip_select == 9:
            if drip_point == 1:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper9()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_1st_pos()

            elif drip_point == 2:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper9()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_2nd_pos()

            elif drip_point == 3:
                await rc.new_preparing_pick_dripper()
                await rc.new_pick_dripper9()
                await rc.new_ready_for_set_234_floor_dripper()
                await rc.new_set_dripper_3rd_pos()

    async def coffee_drop(self, drop_point, coffee_count):
        await rc.beancup_pick()

        for i in range(int(coffee_count)):
            await rc.beancup_grinding_bean_in()
            time.sleep(2.3)
            await rc.beancup_grinding_bean_out()
        
        if drop_point == 1:
            await rc.beancup_dropbean_ready()
            await rc.beancup_dropbean_1()
            await rc.beancup_dropbean_end()
        elif drop_point == 2:
            await rc.beancup_dropbean_ready()
            await rc.beancup_dropbean_2()
            await rc.beancup_dropbean_end()
        elif drop_point == 3:
            await rc.beancup_dropbean_ready()
            await rc.beancup_dropbean_3()
            await rc.beancup_dropbean_end()
        
        await rc.beancup_back()

        if drop_point == 1:
            await rc.shaking_dripper1()
        elif drop_point == 2:
            await rc.shaking_dripper2()
        elif drop_point == 3:
            await rc.shaking_dripper3()

    async def cup_set_move(self, cup_point): 
        await rc.pick_the_cup_s()
        await cd.cup_out()
        await asyncio.sleep(2)
        await rc.pick_the_cup_f()

        if cup_point == 1:
            await rc.new_set_cup1()

        elif cup_point == 2:
            await rc.new_set_cup2()

        elif cup_point == 3:
            await rc.new_set_cup3()

    async def water_move(self, temp_info, temp):
        if temp_info == 'ok': 
            await tm.trigger_output(1)
            await rc.kettle_pick()
        else:
            await self.temp_S(temp)
            while True:
                msg = await self.temp_M()
                if msg == 'ok':
                    break
                await asyncio.sleep(1)

            await tm.trigger_output(1)
            await rc.kettle_pick()

    async def drip_water(self, drip_point, type_re, wm, wmc, tm, tmc):
        i = 0
        SPEED = 100
        wm = [int(w.strip()) for w in wm.split(',')]
        tm = [int(t.strip()) for t in tm.split(',')]
        if drip_point == 1:
            if type_re == '0': # 그냥 붓기
                for w in range(wmc):
                    print(w)
                    now = time.localtime()
                    if wm[i] == 40:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = -0.72 * i# j5
                            ANG_SUB2 = 0.6 * i# j4
                            ANG_SUB3 = -1.2 * i# j3
                            ANG_SUB4 = 0.6 * i# j2
                            ANG_SUB5 = -0.72 * i# j1
                        else:
                            ANG = 1.5 * i
                            ANG_SUB1 = -0.72 * i# j5
                            ANG_SUB2 = 0.6 * i# j4
                            ANG_SUB3 = -1.2 * i# j3
                            ANG_SUB4 = 0.6 * i# j2
                            ANG_SUB5 = -0.72 * i# j1

                    elif wm[i] == 50:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = -0.96 * i# j5
                            ANG_SUB2 = 0.8 * i# j4
                            ANG_SUB3 = -1.6 * i# j3
                            ANG_SUB4 = 0.8 * i# j2
                            ANG_SUB5 = -0.96 * i# j1
                            
                        else:
                            ANG = 2 * i
                            ANG_SUB1 = -0.96 * i# j5
                            ANG_SUB2 = 0.8 * i# j4
                            ANG_SUB3 = -1.6 * i# j3
                            ANG_SUB4 = 0.8 * i# j2
                            ANG_SUB5 = -0.96 * i# j1

                    elif wm[i] == 60:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = -1.44 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -2.4 * i# j3
                            ANG_SUB4 = 1.2 * i# j2
                            ANG_SUB5 = -1.44 * i# j1
                        else:
                            ANG = 3 * i
                            ANG_SUB1 = -1.44 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -2.4 * i# j3
                            ANG_SUB4 = 1.2 * i# j2
                            ANG_SUB5 = -1.44 * i# j1
                    else:
                        ANG = 1
                        ANG_SUB1 = -0.48 * i# j5
                        ANG_SUB2 = 0.4 * i# j4
                        ANG_SUB3 = -0.8 * i# j3
                        ANG_SUB4 = 0.4 * i# j2
                        ANG_SUB5 = -0.48 * i# j1
                        
                    await rc.standard_pour1(ANG, ANG_SUB1, ANG_SUB2, ANG_SUB3, ANG_SUB4, ANG_SUB5)
                    next = time.localtime()
                    time_difference = time.mktime(next) - time.mktime(now)
                    
                    print(float(tm[i]))
                    print(float(tm[i])-time_difference)
                    await asyncio.sleep(float(tm[i])-time_difference)
                    i =+ 1
            else: # 스파이럴 붓기
                for w in range(wmc):
                    now = time.localtime()
                    if wm[i] == 40:
                        if i == 0:
                            ANG = 1.5 * i
                            ANG_SUB1 = -0.72 * i# j5
                            ANG_SUB2 = 0.6 * i# j4
                            ANG_SUB3 = -1.2 * i# j3
                            ANG_SUB4 = 0.6 * i# j2
                            ANG_SUB5 = -0.72 * i# j1
                        else:
                            ANG = 1.5 * i
                            ANG_SUB1 = -0.72 * i# j5
                            ANG_SUB2 = 0.6 * i# j4
                            ANG_SUB3 = -1.2 * i# j3
                            ANG_SUB4 = 0.6 * i# j2
                            ANG_SUB5 = -0.72 * i# j1

                    elif wm[i] == 50:
                        if i == 0:
                            ANG = 2 * i
                            ANG_SUB1 = -0.96 * i# j5
                            ANG_SUB2 = 0.8 * i# j4
                            ANG_SUB3 = -1.6 * i# j3
                            ANG_SUB4 = 0.8 * i# j2
                            ANG_SUB5 = -0.96 * i# j1
                            
                        elif i == 1 or i == 2:
                            ANG = 2 * i
                            ANG_SUB1 = -0.96 * i# j5
                            ANG_SUB2 = 0.8 * i# j4
                            ANG_SUB3 = -1.6 * i# j3
                            ANG_SUB4 = 0.8 * i# j2
                            ANG_SUB5 = -0.96 * i# j1

                        elif i == 3 or i == 4:
                            ANG = 2 * i + 0.5
                            ANG_SUB1 = -0.96 * i# j5
                            ANG_SUB2 = 0.8 * i# j4
                            ANG_SUB3 = -1.6 * i# j3
                            ANG_SUB4 = 0.8 * i# j2
                            ANG_SUB5 = -0.96 * i# j1
                        
                        elif i >= 5:
                            ANG = 2 * i + 0.75
                            ANG_SUB1 = -0.96 * i# j5
                            ANG_SUB2 = 0.8 * i# j4
                            ANG_SUB3 = -1.6 * i# j3
                            ANG_SUB4 = 0.8 * i# j2
                            ANG_SUB5 = -0.96 * i# j1

                    elif wm[i] == 60:
                        if i == 0:
                            ANG = 3 * i
                            ANG_SUB1 = -1.44 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -2.4 * i# j3
                            ANG_SUB4 = 1.2 * i# j2
                            ANG_SUB5 = -1.44 * i# j1
                        else:
                            ANG = 3 * i
                            ANG_SUB1 = -1.44 * i# j5
                            ANG_SUB2 = 1.5 * i# j4
                            ANG_SUB3 = -3 * i# j3
                            ANG_SUB4 = 1.5 * i# j2
                            ANG_SUB5 = -1.44 * i# j1
                    else:
                        ANG = 1
                        ANG_SUB1 = -0.48 * i# j5
                        ANG_SUB2 = 0.4 * i# j4
                        ANG_SUB3 = -0.8 * i# j3
                        ANG_SUB4 = 0.4 * i# j2
                        ANG_SUB5 = -0.48 * i# j1

                    await rc.standard_spiral1(SPEED, ANG, ANG_SUB1, ANG_SUB2, ANG_SUB3, ANG_SUB4, ANG_SUB5)
                    next = time.localtime()
                    time_difference = time.mktime(next) - time.mktime(now)
                    print("소요시간 : ",time_difference)
                    print(float(tm[i]))
                    print(float(tm[i])-time_difference)
                    await asyncio.sleep(float(tm[i])-time_difference)
                    i =+ 1
        elif drip_point == 2:
            if type_re == '0': # 그냥 붓기
                for w in range(wmc):
                    now = time.localtime()
                    if wm[i] == 40:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.075 * i# j5
                            ANG_SUB2 = 0.9 * i# j4
                            ANG_SUB3 = -0.75 * i# j3
                        else:
                            ANG = 1.5 * i
                            ANG_SUB1 = 0.075 * i# j5
                            ANG_SUB2 = 0.9 * i# j4
                            ANG_SUB3 = -0.75 * i# j3

                    elif wm[i] == 50:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3
                            
                        elif i == 1 or i == 2:
                            ANG = 2 * i
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3
                        
                        elif i == 3 or i == 4:
                            ANG = 2 * i + 0.5
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3
                        
                        elif i >= 5:
                            ANG = 2 * i + 0.75
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3
                        
                    elif wm[i] == 60:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.3 * i# j5
                            ANG_SUB2 = 1.8 * i# j4
                            ANG_SUB3 = -1.5 * i# j3
                        else:
                            ANG = 3 * i
                            ANG_SUB1 = 0.3 * i# j5
                            ANG_SUB2 = 1.8 * i# j4
                            ANG_SUB3 = -1.5 * i# j3
                    else:
                        ANG = 1
                        ANG_SUB1 = 0.1 * i# j5
                        ANG_SUB2 = 0.6 # j4
                        ANG_SUB3 = -0.5 * i# j3
                    await rc.standard_pour2(ANG, ANG_SUB1, ANG_SUB2, ANG_SUB3)
                    next = time.localtime()
                    time_difference = time.mktime(next) - time.mktime(now)
                    await asyncio.sleep(float(tm[i])-time_difference)
                    i =+ 1
            else:      
                for w in range(wmc):
                    now = time.localtime()
                    if wm[i] == 40:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.075 * i# j5
                            ANG_SUB2 = 0.9 * i# j4
                            ANG_SUB3 = -0.75 * i# j3
                        else:
                            ANG = 1.5 * i
                            ANG_SUB1 = 0.075 * i# j5
                            ANG_SUB2 = 0.9 * i# j4
                            ANG_SUB3 = -0.75 * i# j3

                    elif wm[i] == 50:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3
                            
                        elif i == 1 or i == 2:
                            ANG = 2 * i
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3

                        elif i == 3 or i == 4:
                            ANG = 2 * i + 0.5
                            ANG_SUB1 = (0.2 * i)+0.05# j5
                            ANG_SUB2 = (1.2 * i)+0.3# j4
                            ANG_SUB3 = (-1 * i)+0.25# j3
                        
                        elif i >= 5:
                            ANG = 2 * i + 0.75
                            ANG_SUB1 = (0.2 * i)+0.075# j5
                            ANG_SUB2 = (1.2 * i)+0.45# j4
                            ANG_SUB3 = (-1 * i)+0.375# j3

                    elif wm[i] == 60:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.3 * i# j5
                            ANG_SUB2 = 1.8 * i# j4
                            ANG_SUB3 = -1.5 * i# j3
                        else:
                            ANG = 3 * i
                            ANG_SUB1 = 0.3 * i# j5
                            ANG_SUB2 = 1.8 * i# j4
                            ANG_SUB3 = -1.5 * i# j3
                    else:
                        ANG = 1
                        ANG_SUB1 = 0.1 * i# j5
                        ANG_SUB2 = 0.6 # j4
                        ANG_SUB3 = -0.5 * i# j3
                    await rc.standard_spiral2(SPEED, ANG, ANG_SUB1, ANG_SUB2, ANG_SUB3)
                    next = time.localtime()
                    time_difference = time.mktime(next) - time.mktime(now)
                    await asyncio.sleep(float(tm[i])-time_difference)
                    i =+ 1
        elif drip_point == 3:
            if type_re == '0': # 그냥 붓기
                for w in range(wmc):
                    now = time.localtime()
                    if wm[i] == 40:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.1 * i# j5
                            ANG_SUB2 = 0.6 # j4
                            ANG_SUB3 = -0.5 * i# j3
                        else:
                            ANG = 1.5 * i
                            ANG_SUB1 = 0.1 * i# j5
                            ANG_SUB2 = 0.6 # j4
                            ANG_SUB3 = -0.5 * i# j3
                    elif wm[i] == 50:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.1 * i# j5
                            ANG_SUB2 = 0.6 # j4
                            ANG_SUB3 = -0.5 * i# j3
                        else:
                            ANG = 2 * i
                            ANG_SUB1 = 0.1 * i# j5
                            ANG_SUB2 = 0.6 # j4
                            ANG_SUB3 = -0.5 * i# j3
                    elif wm[i] == 60:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.1 * i# j5
                            ANG_SUB2 = 0.6 # j4
                            ANG_SUB3 = -0.5 * i# j3
                        else:
                            ANG = 3 * i
                            ANG_SUB1 = 0.1 * i# j5
                            ANG_SUB2 = 0.6 # j4
                            ANG_SUB3 = -0.5 * i# j3
                    else:
                        ANG = 1
                        ANG_SUB1 = 0.1 * i# j5
                        ANG_SUB2 = 0.6 # j4
                        ANG_SUB3 = -0.5 * i# j3
                    await rc.standard_pour3(ANG, ANG_SUB1, ANG_SUB2, ANG_SUB3)
                    next = time.localtime()
                    time_difference = time.mktime(next) - time.mktime(now)
                    await asyncio.sleep(float(tm[i])-time_difference)
                    i =+ 1
            else:      
                for w in range(wmc):
                    now = time.localtime()
                    if wm[i] == 40:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.075 * i# j5
                            ANG_SUB2 = 0.9 * i# j4
                            ANG_SUB3 = -0.75 * i# j3
                        else:
                            ANG = 1.5 * i
                            ANG_SUB1 = 0.075 * i# j5
                            ANG_SUB2 = 0.9 * i# j4
                            ANG_SUB3 = -0.75 * i# j3

                    elif wm[i] == 50:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3
                            
                        elif i == 1 or i == 2:
                            ANG = 2 * i
                            ANG_SUB1 = 0.2 * i# j5
                            ANG_SUB2 = 1.2 * i# j4
                            ANG_SUB3 = -1 * i# j3

                        elif i == 3 or i == 4:
                            ANG = 2 * i + 0.5
                            ANG_SUB1 = (0.2 * i)+0.05# j5
                            ANG_SUB2 = (1.2 * i)+0.3# j4
                            ANG_SUB3 = (-1 * i)+0.25# j3
                        
                        elif i >= 5:
                            ANG = 2 * i + 0.75
                            ANG_SUB1 = (0.2 * i)+0.075# j5
                            ANG_SUB2 = (1.2 * i)+0.45# j4
                            ANG_SUB3 = (-1 * i)+0.375# j3

                    elif wm[i] == 60:
                        if i == 0:
                            ANG = 0
                            ANG_SUB1 = 0.3 * i# j5
                            ANG_SUB2 = 1.8 * i# j4
                            ANG_SUB3 = -1.5 * i# j3
                        else:
                            ANG = 3 * i
                            ANG_SUB1 = 0.3 * i# j5
                            ANG_SUB2 = 1.8 * i# j4
                            ANG_SUB3 = -1.5 * i# j3
                    else:
                        ANG = 1
                        ANG_SUB1 = 0.1 * i# j5
                        ANG_SUB2 = 0.6 # j4
                        ANG_SUB3 = -0.5 * i# j3
                    await rc.standard_spiral3(SPEED, ANG, ANG_SUB1, ANG_SUB2, ANG_SUB3)
                    next = time.localtime()
                    time_difference = time.mktime(next) - time.mktime(now)
                    await asyncio.sleep(float(tm[i])-time_difference)
                    i =+ 1
        print("drip end")
        
        await rc.pouring_water()
        await asyncio.sleep(2)
        await rc.kettle_back()

    async def drip_clearing(self, drip_point): # 드리퍼 꺼냈던 위치로 재배치
        drip_select = await Or.check_dripback_select()
        if drip_select == 1:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                           
                await rc.back_pick_dripper1()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper1()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper1()

        elif drip_select == 2:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper2()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper2()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper2()
            
        elif drip_select == 3:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper3()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper3()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper3()
            
        elif drip_select == 4:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper4()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper4()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper4()
            
        elif drip_select == 5:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper5()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper5()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper5()
            
        elif drip_select == 6:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper6()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper6()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper6()
            
        elif drip_select == 7:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper7()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper7()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper7()
            
        elif drip_select == 8:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper8()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper8()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper8()
            
        elif drip_select == 9:
            if drip_point == '1':
                await rc.back_dripper_1st_pos()
                
                await rc.back_pick_dripper9()

            elif drip_point == '2':
                await rc.back_dripper_2nd_pos()

                await rc.back_pick_dripper9()

            elif drip_point == '3':
                await rc.back_dripper_3rd_pos()

                await rc.back_pick_dripper9()
        await Or.update_drip_f2(int(drip_point))
        await Or.update_drip_point_f(drip_select)
        await rc.set_home()

async def listen(listener_node):
    uri = "ws://192.168.58.8:9090"
    async with websockets.connect(uri) as websocket:
        subscribe_msg = {
            "op": "subscribe",
            "topic": "/drip",
            "type": "std_msgs/String"
        }
        await websocket.send(json.dumps(subscribe_msg))

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(data)
            if 'msg' in data:
                await listener_node.listener_callback(data['msg'])
            
def main(args=None):
    rclpy.init(args=args)
    listener = Listener()
    asyncio.get_event_loop().run_until_complete(listen(listener))
    rclpy.spin(listener)
    listener.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
