"#-*- coding: UTF-8 -*-"
import sys
sys.path.append('~/ros_ws/src/Ajou_Drip_Project-main/ROS2_Foxy')
import asyncio
import websockets # type: ignore
import json
import time
import socketio

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

#비전 데이터 
dripper_data = []
cup_data = []
#order_service Flask server(주문 받는 서버) 주소
FLASK_SERVER_URI = 'ws://192.168.58.27:5555'
VISION_SERVER_URI = 'ws://192.168.58.'

# 비동기 Socket.IO 클라이언트 생성
sio_flask = socketio.AsyncClient()
sio_vision = socketio.AsyncClient()

class Listener(Node):
    step = 0
    def __init__(self):
        super().__init__('listener')
        self.publisher = self.create_publisher(String, '/robot', 10)
        ### sub
        self.sub_check = self.create_subscription(
            String, 'pos', self.listener_callback, 10)
        self.sub_check
        self.subscription_order = self.create_subscription(
            String, 'order', self.listener_callback, 10)
        self.subscription_vision = self.create_subscription(
            String, 'vision', self.listener_vision_callback, 10)
        
        self.subscription_order
        self.subscription_vision

        self.lock = asyncio.Lock()  

        self.websocket_uri = "ws://192.168.58.27:9090"
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
            
    async def listener_vision_callback(self, msg):
        async with self.lock:
            print("GOT VISION TOPIC")
            data = msg['data'].strip()
            data = data.replace("'", '"')
            data = json.loads(data)
            self.get_logger().info(f"Received raw data: {data}") 

            # dripper 데이터 초기화 및 저장
            dripper_data.clear()
            for dripper in data['dripper']:
                single_dripper_data = {}
                single_dripper_data['order'] = dripper.get('order')
                
                # 좌표 정보 가져오기
                coor = dripper.get('coordinate')
                single_dripper_data['coordinate'] = coor if coor else []

                # center 정보 가져오기
                center = dripper.get('center')
                single_dripper_data['center'] = center if center else []

                # 존재 여부 정보
                single_dripper_data['exist_dripper'] = dripper.get('exist_dripper')
                single_dripper_data['exist_coffee_beans'] = dripper.get('exist_coffee_beans')

                # dripper_data 리스트에 추가
                dripper_data.append(single_dripper_data)

        # cup 데이터 초기화 및 저장
        cup_data.clear()
        for cup in data['cup']:
            single_cup_data = {}
            single_cup_data['order'] = cup.get('order')
            
            # 좌표 정보 가져오기
            coor = cup.get('coordinate')
            single_cup_data['coordinate'] = coor if coor else []

            # center 정보 가져오기
            center = cup.get('center')
            single_cup_data['center'] = center if center else []

            # 존재 여부 정보
            single_cup_data['exist_cup'] = cup.get('empty')

            # cup_data 리스트에 추가
            cup_data.append(single_cup_data)

        self.get_logger().info(f"Processed dripper data: {dripper_data}")
        self.get_logger().info(f"Processed cup data: {cup_data}")     
                
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
                    #await self.drip_clearing(sub_msg2)
                    print("await self.drip_clearing(sub_msg2)")
            else: 
                await sio_flask.connect(FLASK_SERVER_URI)
                await sio_vision.connect(VISION_SERVER_URI) 
                
                await self.recipe_dripper(msg_Coffee, msg_Type, msg_Temp, msg_WTotal, msg_WM, len(recipe_w), msg_TM, len(recipe_t))


    ## 제어메인, 수정 필요        
    async def recipe_dripper(self, coffee, type, temp, wtotal, wm, wmc, tm, tmc):
        coffee_count = int(coffee)/2 #이거 왜 나누지?
        current_step = 0
        self.progress_info(current_step)
        
                # Define a coroutine to wait for the `vision_get` message and set `vision_ok` to 1
        async def wait_for_vision():
            vision_ok = 0  # Default value before receiving the message

            @sio_vision.on('vision_get')
            async def on_vision_get(data):
                nonlocal vision_ok
                vision_ok = 1
                print("Received vision_get message")
            
            # Wait for the `vision_get` event to be received
            while vision_ok == 0:
                await asyncio.sleep(0.1)
            
            return vision_ok
    
        #vision에 데이터 요청
        asyncio.run_coroutine_threadsafe(self.request_vision_current_data(), self.loop)
        
        vision_ok, drip_point, cup_point = await asyncio.gather(
            wait_for_vision(),
            Or.check_drip_point(dripper_data), #drip할 위치 확인
            Or.check_cup_point(cup_data)
        )
        
        if vision_ok:
            current_step = 4 #진행 step 업데이트
            self.progress_info(current_step)

            if drip_point and cup_point == None:  # drip할 위치 정해지지 않은 경우, 로봇 진행대기 상태
                msg = '진행대기'
                self.publish_msg_robot(msg) #진행 대기 상태 보고
            
            else:
                if coffee == 1: # 전주연 레시피
                    await self.coffee_drop(drip_point, coffee_count)
                    current_step = 8
                    self.progress_info(current_step)

                    #await self.cup_set_move(order_set3)
                    await rc.kettle_pick()
                    current_step = 15
                    self.progress_info(current_step)

                    #await self.water_move(order_set2, temp)
                    await rc.pouring_water()
                    current_step = 20
                    self.progress_info(current_step)

                    #await self.drip_water(order_set3, type, wm, wmc, tm, tmc)
                    await rc.pouring_water_home()
                    await rc.pouring_water_dripper1()
                    current_step = 24
                    self.progress_info(current_step)

                    await rc.kettle_back()
                    current_step = 29
                    self.progress_info(current_step)

                    await rc.set_home()
                    current_step = 30
                    self.progress_info(current_step)
      
                    print("finish")
                    current_step = 31
                    self.progress_info(current_step)
                
                elif coffee == 2: #테츠 카츠야
                    print("테츠 카츠야 레시피")
    
    def progress_info(self, step):
        # TOTAL_STEP = 31
        # pr = (step / TOTAL_STEP) * 100  # 진행률 계산

        # ROS2 WebSocket으로 진행률 데이터를 보내는 함수 호출
        asyncio.run_coroutine_threadsafe(self.send_websocket_progress(step), self.loop)
        
    # 서버에 연결 시 호출되는 이벤트 핸들러
    @sio_flask.event
    async def connect():
        print("Connected to Flask server")

    @sio_vision.event
    async def connect():
        print("Connected to Vision server")
        
    # 서버와의 연결 해제 시 호출되는 이벤트 핸들러
    @sio_flask.event
    async def disconnect():
        print("Disconnected from Flask server")
    
    @sio_vision.event
    async def disconnect():
        print("Disconnected from Vision server")
    
        # 진행률 데이터를 서버로 전송하는 함수
    async def send_websocket_progress(self, progress):
        try:
            message = {
                "op": "progress_update",
                "progress": progress
            }
            # 서버로 진행률 데이터 전송
            await sio_flask.emit('progress_update', message)
            print(f'Progress sent to Flask Server: {message}')
        except Exception as e:
            print(f"Failed to send progress to Flask Server: {str(e)}")
    
    async def request_vision_current_data():
        try:
            sio_vision.emit('data plz')
            print('Requested vision data to vision server')
        except Exception as e:
            print("Failed to request to Vision server")
            
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

    async def coffee_drop(self, drop_point, coffee_count, cup_point): ##원두 to 드리퍼 이동
        if cup_point == 1:
            await rc.beancup_pick1() #원두컵 집기, 
            if drop_point == 1:
                await rc.beancup_dropbean_ready()
                await rc.beancup_dropbean_1()
                await rc.beancup_back1() #원두컵 복귀
                await rc.new_preparing_pick_dripper()
                await rc.shaking_dripper1()
                
            elif drop_point == 2:
                await rc.beancup_dropbean_ready() 
                await rc.beancup_dropbean_2() 
                await rc.beancup_back2() #원두컵 복귀
                await rc.new_preparing_pick_dripper()
                await rc.shaking_dripper2()
            elif drop_point == 3:
                await rc.beancup_dropbean_ready() 
                await rc.beancup_dropbean_3() 
                await rc.beancup_back3() #원두컵 복귀
                await rc.new_preparing_pick_dripper()
                await rc.shaking_dripper3()
                
        elif cup_point == 2:
            await rc.beancup_pick2()
            
            if drop_point == 1:
                    await rc.beancup_dropbean_ready()
                    await rc.beancup_dropbean_1()
                    await rc.beancup_back1() #원두컵 복귀
                    await rc.new_preparing_pick_dripper()
                    await rc.shaking_dripper1()
            elif drop_point == 2:
                    await rc.beancup_dropbean_ready() 
                    await rc.beancup_dropbean_2() 
                    await rc.beancup_back2() #원두컵 복귀
                    await rc.new_preparing_pick_dripper()
                    await rc.shaking_dripper2()
            elif drop_point == 3:
                    await rc.beancup_dropbean_ready() 
                    await rc.beancup_dropbean_3() 
                    await rc.beancup_back3() #원두컵 복귀
                    await rc.new_preparing_pick_dripper()
                    await rc.shaking_dripper3()
        elif cup_point == 3:
            await rc.beancup_pick3()
            
            if drop_point == 1:
                    await rc.beancup_dropbean_ready()
                    await rc.beancup_dropbean_1()
                    await rc.beancup_back1() #원두컵 복귀
                    await rc.new_preparing_pick_dripper()
                    await rc.shaking_dripper1()
            elif drop_point == 2:
                    await rc.beancup_dropbean_ready() 
                    await rc.beancup_dropbean_2() 
                    await rc.beancup_back2() #원두컵 복귀
                    await rc.new_preparing_pick_dripper()
                    await rc.shaking_dripper2()
            elif drop_point == 3:
                    await rc.beancup_dropbean_ready() 
                    await rc.beancup_dropbean_3() 
                    await rc.beancup_back3() #원두컵 복귀
                    await rc.new_preparing_pick_dripper()
                    await rc.shaking_dripper3()
        
        # if drop_point == 1:
        #     await rc.beancup_dropbean_ready()
        #     await rc.beancup_dropbean_1()
        #     await rc.beancup_dropbean_end()
        # elif drop_point == 2:
        #     await rc.beancup_dropbean_ready()
        #     await rc.beancup_dropbean_2()
        #     await rc.beancup_dropbean_end()
        # elif drop_point == 3:
        #     await rc.beancup_dropbean_ready()
        #     await rc.beancup_dropbean_3()
        #     await rc.beancup_dropbean_end()
        
        # await rc.beancup_back() #원두컵 복귀

        # if drop_point == 1: #원두 평탄화
        #     await rc.shaking_dripper1()
        # elif drop_point == 2:
        #     await rc.shaking_dripper2()
        # elif drop_point == 3:
        #     await rc.shaking_dripper3()

    #cup 어디서 pick할지 ..?
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
    #일단 temp_s, temp_m 안쓰는 방향으로 고려필요
    async def water_move(self, temp_info, temp): #수정필요!! nfc 정수기 사용하면 급수 기다리는 구문 추가 필요!!
        ## 여기부터 불필요
        if temp_info == 'ok': #수정필요 !! temp 사용안할거면 if없이 가야함
            await tm.trigger_output(1) #await send_at_command(f'AT+OUTPUT={setting}')
            await rc.kettle_pick()
        else:
            await self.temp_S(temp) #온도 체크
            while True: #온도 설정 대기 구문
                msg = await self.temp_M()
                if msg == 'ok':
                    break
                await asyncio.sleep(1)

            await tm.trigger_output(1) #출수 명령
            ##여기까지 
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

        #drip_clearing 삭제 Complete_24.10.28, 
        await Or.update_drip_f2(int(drip_point))
        await Or.update_drip_point_f(drip_select)
        await rc.set_home()

async def listen_order(listener_node):
    uri = "ws://192.168.58.27:9090"
    async with websockets.connect(uri) as websocket:
        subscribe_msg = {
                "op": "subscribe",
                "topic": "/order",
                "type": "std_msgs/String"
            }
        await websocket.send(json.dumps(subscribe_msg))
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(data)
            if 'msg' in data:
                await listener_node.listener_callback(data['msg'])

async def listen_vision(listener_node):
    uri = "ws://192.168.58.27:9090"
    async with websockets.connect(uri) as websocket:
        subscribe_msg = {
                "op": "subscribe",
                "topic": "/vision",
                "type": "std_msgs/String"
            }
        await websocket.send(json.dumps(subscribe_msg))
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(data)
            if 'msg' in data:
                await listener_node.listener_vision_callback(data['msg'])
        
def main(args=None):
    rclpy.init(args=args)
    listener = Listener()
    #asyncio.get_event_loop().run_until_complete(listen_vision(listener))
    #asyncio.get_event_loop().run_until_complete(listen_order(listener))
    asyncio.get_event_loop().run_until_complete(asyncio.gather(listen_order(listener),listen_vision(listener)))
    rclpy.spin(listener)
    listener.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
