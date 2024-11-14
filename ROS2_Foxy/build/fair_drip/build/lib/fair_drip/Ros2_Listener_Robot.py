"#-*- coding: UTF-8 -*-"
import sys
sys.path.append('~/ros_ws/src/Ajou_Drip_Project-main/ROS2_Foxy')
import asyncio
import websockets # type: ignore
import json
import time
import socketio
import pyttsx3

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
import fair_drip.control_Temp_M as tm
import fair_drip.control_Order as Or

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
#order_service Flask server(주문 받는 서버) 주소s
FLASK_SERVER_URI = 'ws://192.168.58.13:5555'
VISION_SERVER_URI = 'ws://192.168.58.25:9999'
#SERVING_SERVER_URI = 'ws://192.168.58.26:5000'
# 비동기 Socket.IO 클라이언트 생성
sio_flask = socketio.AsyncClient()
sio_vision = socketio.AsyncClient()
#sio_serving = socketio.AsyncClient()

vision_ok = 0
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

        global vision_ok
        global dripper_data
        global cup_data
        
        
        self.lock = asyncio.Lock()  

        self.websocket_uri = "ws://192.168.58.13:9090"
        
        
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
        print("CALLBACK : GOT VISION TOPIC")
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
            single_cup_data['exist_cup'] = cup.get('exist_cup')

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
                print("Failed to get Coffee Data")
            else: 
                await sio_flask.connect(FLASK_SERVER_URI)
                await sio_vision.connect(VISION_SERVER_URI) 
                #await sio_serving.connect(SERVING_SERVER_URI)
                await self.recipe_dripper(msg_Coffee, msg_Type, msg_Temp, msg_WTotal, msg_WM, len(recipe_w), msg_TM, len(recipe_t))
                # Define a coroutine to wait for the `vision_get` message and set `vision_ok` to 1
    
    ## 제어메인, 수정 필요  
    # Or 모듈에서 check_drip_point 함수 정의
    async def check_drip_point(self, dripper_data):
        # 조건에 맞는 dripper 데이터를 필터링
        print("CHECK_DRIP_POINT")
        print(dripper_data)
        valid_drippers = [
            dripper['order'] for dripper in dripper_data
            if dripper.get('exist_dripper') or dripper.get('exist_coffee_beans')
        ]
        # order 값이 가장 작은 dripper 선택
        print("---------------------------------------------------------------")
        print(valid_drippers)
        return min(valid_drippers) if valid_drippers else None

    # Or 모듈에서 check_cup_point 함수 정의
    async def check_cup_point(self, cup_data):
        # 조건에 맞는 cup 데이터를 필터링
        valid_cups = [
            cup['order'] for cup in cup_data
            if cup.get('exist_cup')
        ]
        # order 값이 가장 작은 cup 선택
        if valid_cups is None:  
            print("NO valid Cup")
        print(f'valid_cup : {min(valid_cups)}')
        return min(valid_cups) if valid_cups else None

    async def recipe_dripper(self, coffee, type, temp, wtotal, wm, wmc, tm, tmc):
        current_step = 0
        self.progress_info(current_step)
        
        #vision에 데이터 요청
        asyncio.run_coroutine_threadsafe(self.request_vision_current_data(), self.loop)
        #sleep(0.5)
                
        print()  # vision_ok가 1이 되면 줄바꿈
        i = 0
        while vision_ok != 1 :
            if i < 10:
                print('.', end='', flush=True)  # 줄바꿈 없이 출력
                await asyncio.sleep(1)  # 비동기적으로 1초 대기
                i += 1
            else: 
                i = 0
        print()  # vision_ok가 1이 되면 줄바꿈
        
        drip_point, cup_point= await asyncio.gather(
            self.check_drip_point(dripper_data), #drip할 위치 확인
            self.check_cup_point(cup_data)       #Cup위치 확인
        )

        # drop_point, cup_point 1 / 2 / 3 check

        if vision_ok:
            current_step = 4 #진행 step 업데이트
            self.progress_info(current_step)

            if (drip_point and cup_point) is None:  
                print("Drip point and Cup Point is not chosen.\nPlease Check one more time")
                time.sleep(1)
                return await self.recipe_dripper(coffee, type, temp, wtotal, wm, wmc, tm, tmc)
            else:
                if coffee == 1: # 전주연 레시피
                    print("home gaza~~~~")
                    print(f'Drip Point: {dripper_data}\nCup Point: {cup_data}')
                    await rc.set_home()
                    #원두컵 집고 드립퍼에 붓기
                    await self.coffee_drop(drip_point, cup_point)
                    current_step = 10
                    self.progress_info(current_step)
                    
                      #주전자 집기
                    await rc.kettle_pick()
                    current_step = 25
                    self.progress_info(current_step)
 
                      #물 붓기
                    await rc.pouring_water()
                    current_step = 45
                    self.progress_info(current_step)

                      #레시피 만큼 얼마나 기다리는지, 물을 얼마나 붓는지.
                    await rc.pouring_water_home()
                    self.loop.create_task(self.speaking('Pouring water. Please wait. This is not Error human.'))
                    await rc.spiral_dripper(drip_point)
                    current_step = 65
                    self.progress_info(current_step)
 
                      #주전자 원위치
                    await rc.kettle_back()
                    current_step = 75
                    self.progress_info(current_step)


                    cureent_step = 90
                    await rc.delivery(drip_point)
                    self.progress_info(current_step)
 
                      #손 원위치
                    await rc.set_home()
                    current_step = 95
                    self.progress_info(current_step)
                    self.speaking("zz")
                    print("finish")
                    current_step = 100
                    self.progress_info(current_step)
                    
                    self.Send_to_Serving('hello')
                    
                elif coffee == 2: #테츠 카츠야
                    print("테츠 카츠야 레시피")
                    #self.Send_to_Serving()


    def progress_info(self, step):
        # TOTAL_STEP = 31
        # pr = (step / TOTAL_STEP) * 100  # 진행률 계산
        # ROS2 WebSocket으로 진행률 데이터를 보내는 함수 호출
        asyncio.run_coroutine_threadsafe(self.send_websocket_progress(step), self.loop)
    async def speaking(self, txt_en):
        engine = pyttsx3.init()

        engine.setProperty('rate',200)
        engine.say(txt_en)
        engine.runAndWait()

    # 서버에 연결 시 호출되는 이벤트 핸들러
    @sio_flask.event
    async def connect():
        print("Connected to Flask server")

    @sio_vision.event
    async def connect():
        print("Connected to Vision server")
        
    #@sio_serving.event
    #async def connect():
        #print("Connected to Serving server")
        
    # 서버와의 연결 해제 시 호출되는 이벤트 핸들러
    @sio_flask.event
    async def disconnect():
        print("Disconnected from Flask server")
    
    @sio_vision.event
    async def disconnect():
        print("Disconnected from Vision server")

    #@sio_serving.event
    #async def disconnect():
        #print("Disconnected from Serving server")
    
    @sio_vision.on('vision_get')
    async def on_vision_get():
        global vision_ok
        vision_ok = 1
        print("Received vision_get message")
        
        
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

    async def request_vision_current_data(self):
        try:
            await sio_vision.emit('data plz')
            print('Requested vision data to vision server')
        except Exception as e:  
            print(f"Failed to request to Vision server : {str(e)}")
            
    async def Send_to_Serving(self,msg):
        try:
            #await sio_serving.emit('Done',msg)
            print('Send done to Serving server')
        except Exception as e:  
            print(f"Failed to request to Serving server : {str(e)}")
            
    async def wait_for_vision(self):
        i = 0
        while self.vision_ok != 1:
            if i < 10:
                print('.', end='', flush=True)  # 줄바꿈 없이 출력
                time.sleep(1)  # 비동기적으로 1초 대기
                i += 1
            else: 
                i = 0
        print()  # vision_ok가 1이 되면 줄바꿈
    
    def time_check():
        now = time.localtime()
        f_now = time.strftime("%H:%M:%S", now)

        return f_now

    async def send_websocket_message(self, message):
        if self.websocket.open:
            await self.websocket.send(message)  
            self.get_logger().info(f'Published to WebSocket: {message}')

    async def coffee_drop(self, drop_point, cup_point): ##원두 to 드리퍼 이동
        await rc.beancup_pick(cup_point)
        await rc.beancup_dropbean_ready()
        await rc.beancup_dropbean(drop_point)
        await rc.beancup_back(cup_point)
        await rc.new_preparing_pick_dripper()
        await rc.shaking_dripper(drop_point)
        await rc.new_preparing_pick_dripper()


        
async def listen_order(listener_node):
    uri = "ws://192.168.58.13:9090"
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
    uri = "ws://192.168.58.13:9090"
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
    asyncio.get_event_loop().run_until_complete(asyncio.gather(listen_order(listener),listen_vision(listener)))
    rclpy.spin(listener)
    listener.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
