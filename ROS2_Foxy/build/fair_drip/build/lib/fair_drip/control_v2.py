import os
import numpy as np
import pandas as pd
import time

import asyncio

import conf_file as cf
import frrpc as frrpc
## Robot info
ROBOT_IP = "192.168.58.2" 
robot = frrpc.RPC(ROBOT_IP)


EP=[0.000, 0.000, 0.000, 0.000]
DP=[1.000, 1.000, 1.000, 1.000, 1.000, 1.000]
EP2=[0.000,0.000,0.000,0.000]

async def movecheck():
    while True:
        motion_state = robot.GetRobotMotionDone()
        if motion_state[1] == 1:
            break
        await asyncio.sleep(0.1)

async def SetSpeed( speed):
    robot.SetSpeed(speed)

async def Gripper_open():
    robot.MoveGripper(1, 80, 50, 50, 10000, 0)

async def Gripper_close():
    robot.MoveGripper(1, 25, 50, 50, 10000, 0)

def get_current_joint_positions():
    joint_positions = robot.GetJointState()
    print(f"현재 조인트 위치: {joint_positions}")
    return joint_positions

def transform_pose(joint):
    pose = robot.GetForwardKin(joint)
    cartesian_pose = [pose[1], pose[2], pose[3], pose[4], pose[5], pose[6]]
    return cartesian_pose

def transform_joint(pose):
    joint = robot.GetInverseKin(0, pose, -1)
    joint_pose = [joint[1], joint[2], joint[3], joint[4], joint[5], joint[6]]
    return joint_pose

async def PTP(J=None, SPEED=70.0, BLEND=-1, P=None, retry=2):
    try:
        SPEED = float(SPEED)
        BLEND = float(BLEND)
        if P is None:
            P = transform_pose(J)
        if J is None:
            J = transform_joint(P)
        robot.MoveJ(J, P, 0, 0, SPEED, 100.0, BLEND, EP, -1.0, 0, DP)
    except:
        if (retry > 0):
            PTP(J, 70.0, BLEND, P, retry-1)
            print("execpt : retry PTP")

async def newSPIRAL( J1, SPEED, Pa, DP):

        P1 = transform_pose(J1)
        robot.NewSpiral(J1, P1, 0, 0, float(SPEED), 0.0, EP2, 50.0, 2, DP, Pa)

        while True:
            motion_state = robot.GetRobotMotionDone()
            if motion_state[1] == 1:
                break
                
            await asyncio.sleep(0.1)  

async def movegripper( index, pos, vel, force, max_time, last_arg=0):
    robot.MoveGripper(index, pos, vel, force, max_time, last_arg)
    start_time = time.time()
    while time.time() - start_time < 1.0:  
        gripper_state = robot.GetGripperMotionDone()
        if gripper_state[2] == 1:  
            break
        await asyncio.sleep(0.1) 

async def set_home():
        print("home위치로 이동합니다.")
        robot.MoveGripper(1, 100, 50, 50, 10000, 0)
        await PTP(cf.home_point["J"], 70, -1)
        while True:
            motion_state = robot.GetRobotMotionDone()
            if motion_state[1] == 1:
                break
            await asyncio.sleep(0.1)

async def kettle_pick():
    print("물을 채운 주전자를 집어듭니다.")
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_pick_fullwater_kettle["J91"], 100, -1)
    await PTP(cf.new_pick_fullwater_kettle["J92"], 100, -1)
    await PTP(cf.new_pick_fullwater_kettle["J93"], 100, -1)
    await movegripper(1, 10, 50, 50, 10000, 0)
    await PTP(cf.new_pick_fullwater_kettle["J94"], 50, -1)
    await PTP(cf.new_pick_fullwater_kettle["J95"], 50, -1)
    # await PTP(cf.new_pick_fullwater_kettle["J96"], 30, -1)
    # await PTP(cf.new_pick_fullwater_kettle["J97"], 30, -1)
    # await PTP(cf.new_pick_fullwater_kettle["J98"], 30, -1)
    # await PTP(cf.new_pick_fullwater_kettle["J99"], 30, -1)
    # await PTP(cf.new_pick_fullwater_kettle["J100"], 30, -1)
    # await PTP(cf.new_pick_fullwater_kettle["J101"], 30, -1)
    # await movegripper(1, 100, 50, 50, 10000, 0)

async def kettle_back():
    await PTP(cf.pouring_water["J2"], 30,-1)
    await PTP(cf.pouring_water["J1"], 30,-1)
    await PTP(cf.new_pick_fullwater_kettle["J95"], 50, -1)
    await PTP(cf.new_pick_fullwater_kettle["J94"], 50, -1)
    await PTP(cf.new_pick_fullwater_kettle["J93"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_pick_fullwater_kettle["J92"], 30, -1)
    await PTP(cf.new_pick_fullwater_kettle["J91"], 30, -1)
    

async def pouring_water():
    await PTP(cf.pouring_water["J1"], 30, -1)#물 붓기 Home 가는 중..

async def pouring_water_dripper1():
    await PTP(cf.pouring_water_dripper1["J1"], 100, -1)
    await PTP(cf.pouring_water_dripper1["J2"], 100, -1)
    await asyncio.sleep(4.2)
    await PTP(cf.pouring_water_dripper1["J1"], 100, -1)
    await asyncio.sleep(2)
    await PTP(cf.pouring_water_dripper1["J3"], 100, -1)
    await asyncio.sleep(3.5)
    await PTP(cf.pouring_water_dripper1["J1"], 100, -1)
    await asyncio.sleep(2)
    await PTP(cf.pouring_water_dripper1["J3"], 100, -1)
    await asyncio.sleep(4.3)
    await PTP(cf.pouring_water_dripper1["J1"], 100, -1)
    await asyncio.sleep(2)
    await PTP(cf.pouring_water_dripper1["J4"], 100, -1)
    await asyncio.sleep(3.5)
    await PTP(cf.pouring_water_dripper1["J1"], 100, -1)
    await asyncio.sleep(2)
    await PTP(cf.pouring_water_dripper1["J4"], 100, -1)
    await asyncio.sleep(4)
    await PTP(cf.pouring_water_dripper1["J1"], 100, -1)
    

async def pouring_water_home():
    await PTP(cf.pouring_water["J2"], 50, -1) #물붓기 home 


async def spiral_dripper1():
    await PTP(cf.spiral_dripper1["J1"], 30,-1) 
    await PTP(cf.spiral_dripper1["J2"], 30,-1) 

async def spiral_dripper2():
    await PTP(cf.spiral_dripper2["J1"], 30,-1) 
    await PTP(cf.spiral_dripper2["J2"], 30,-1) 

async def spiral_dripper3():
    await PTP(cf.spiral_dripper3["J1"], 30,-1) 
    await PTP(cf.spiral_dripper3["J2"], 30,-1) 

async def beancup_pick1(): 
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup1['J1'],100, -1) 
    await PTP(cf.pick_bean_cup1['J2'],100, -1)
    await PTP(cf.pick_bean_cup1['J3'],100, -1)
    await PTP(cf.pick_bean_cup1['J4'],100, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup1['J5'],100, -1) 
    await PTP(cf.pick_bean_cup1['J1'],100, -1)

async def beancup_pick2(): 
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup2['J1'],100, -1) 
    await PTP(cf.pick_bean_cup2['J2'],100, -1)
    await PTP(cf.pick_bean_cup2['J3'],100, -1)
    await PTP(cf.pick_bean_cup2['J4'],100, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup2['J5'],100, -1)
    await PTP(cf.pick_bean_cup2['J1'],100, -1)

async def beancup_pick3(): 
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup3['J1'],100, -1) 
    await PTP(cf.pick_bean_cup3['J2'],100, -1)
    await PTP(cf.pick_bean_cup3['J3'],100, -1)
    await PTP(cf.pick_bean_cup3['J4'],100, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup3['J5'],100, -1)
    await PTP(cf.pick_bean_cup3['J1'],100, -1)

async def beancup_back1():
    await PTP(cf.pick_bean_cup1['J1'],100, -1)
    await PTP(cf.pick_bean_cup1['J5'],100, -1)
    await PTP(cf.pick_bean_cup1['J4'],100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup1['J3'],100, -1)
    await PTP(cf.pick_bean_cup1['J1'],100, -1)

async def beancup_back2():
    await PTP(cf.pick_bean_cup2['J1'],100, -1)
    await PTP(cf.pick_bean_cup2['J5'],100, -1)
    await PTP(cf.pick_bean_cup2['J4'],100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup2['J3'],100, -1)
    await PTP(cf.pick_bean_cup2['J1'],100, -1)


async def beancup_back3():
    await PTP(cf.pick_bean_cup3['J1'],100, -1)
    await PTP(cf.pick_bean_cup3['J5'],100, -1)
    await PTP(cf.pick_bean_cup3['J4'],100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup3['J3'],100, -1)
    await PTP(cf.pick_bean_cup3['J1'],100, -1)

async def beancup_grinding_bean_in():
    await PTP(cf.grinding_coffee_bean['J1'],100, -1)

async def beancup_grinding_bean_out():
    await PTP(cf.grinding_coffee_bean['J2'],100, -1)

async def beancup_dropbean_ready():#수정
    await PTP(cf.moving_coffee_bean['J1'], 100, -1)

async def beancup_dropbean1(): #dripper1 수정
    await PTP(cf.set_coffee_bean_dripper1['J1'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J1'], 100, -1)
    await PTP(cf.moving_coffee_bean['J1'], 100, -1)
    
async def beancup_dropbean2(): #수정       
    await PTP(cf.set_coffee_bean_dripper2['J1'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J1'], 100, -1)
    await PTP(cf.moving_coffee_bean['J1'], 100, -1)

async def beancup_dropbean3(): #수정
    await PTP(cf.set_coffee_bean_dripper3['J1'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J4'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J1'], 100, -1)
    await PTP(cf.moving_coffee_bean['J1'], 100, -1)

async def beancup_dropbean_end():
    await PTP(cf.moving_coffee_bean['J3'], 60, -1)
    await PTP(cf.moving_coffee_bean['J2'], 60, -1) 
    await PTP(cf.moving_coffee_bean['J1'], 60, -1)

async def pick_the_cup():
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.home_point["J"],100,-1)
    await PTP(cf.new_pick_the_cup["J1"], 100, -1)
    await PTP(cf.new_pick_the_cup["J2"], 100, -1)
    await PTP(cf.new_pick_the_cup["J3"], 100, -1)
    await PTP(cf.new_pick_the_cup["J4"], 100, -1)
    await PTP(cf.new_pick_the_cup["J5"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await movegripper(1, 30, 50, 50, 10000, 0)
    await PTP(cf.new_pick_the_cup["J6"], 100, -1)
    await PTP(cf.new_pick_the_cup["J7"], 100, -1)
    await PTP(cf.new_pick_the_cup["J8"], 100, -1)
    await PTP(cf.new_pick_the_cup["J9"], 100, -1)

async def pick_the_cup_s():
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_pick_the_cup["J2"], 100, -1)
    await PTP(cf.new_pick_the_cup["J3"], 100, -1)
    await PTP(cf.new_pick_the_cup["J5"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
        
async def pick_the_cup_f():
    await movegripper(1, 30, 50, 50, 10000, 0)
    await PTP(cf.new_pick_the_cup["J6"], 100, -1)
    await PTP(cf.new_pick_the_cup["J7"], 100, -1)
    await PTP(cf.new_pick_the_cup["J8"], 100, -1)
    await PTP(cf.new_pick_the_cup["J9"], 100, -1)

async def new_set_cup1():
    print("컵을 첫번째 자리에 위치합니다.")
    await PTP(cf.new_set_cup1["J1"], 100, -1)
    await PTP(cf.new_set_cup1["J2"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_set_cup1["J3"], 30, -1)
    await PTP(cf.new_set_cup1["J4"], 70, -1)
    await PTP(cf.home_point["J"],100,-1)

async def new_set_cup2():
    print("컵을 두번째 자리에 위치합니다.")
    await PTP(cf.new_set_cup2["J1"], 100, -1)
    await PTP(cf.new_set_cup2["J2"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_set_cup2["J3"], 30, -1)
    await PTP(cf.new_set_cup2["J4"], 70, -1)
    await PTP(cf.home_point["J"],100,-1)

async def new_set_cup3():
    print("컵을 세번째 자리에 위치합니다.")
    await PTP(cf.new_set_cup3["J1"], 100, -1)
    await PTP(cf.new_set_cup3["J2"], 70, -1)
    await PTP(cf.new_set_cup3["J3"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_set_cup3["J4"], 30, -1)
    await PTP(cf.new_set_cup3["J5"], 70, -1)
    await PTP(cf.new_set_cup3["J6"], 100, -1)
    await PTP(cf.home_point["J"],100,-1)

async def new_pick_dripper1():
    print("첫 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper1["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper1["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper1["J3"], 30, -1)
    await PTP(cf.new_pick_dripper1["J4"], 70, -1)
    await PTP(cf.new_pick_dripper1["J5"], 70, -1)

async def new_pick_dripper2():
    print("두 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper2["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper2["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper2["J3"], 30, -1)
    await PTP(cf.new_pick_dripper2["J4"], 70, -1)

async def new_pick_dripper3():
    print("세 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper3["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper3["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper3["J3"], 30, -1)
    await PTP(cf.new_pick_dripper3["J4"], 70, -1)
    await PTP(cf.new_pick_dripper3["J5"], 70, -1)

async def new_pick_dripper4():
    print("네 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper4["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper4["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper4["J3"], 30, -1)
    await PTP(cf.new_pick_dripper4["J4"], 70, -1)
    await PTP(cf.new_pick_dripper4["J5"], 70, -1)

async def new_pick_dripper5():
    print("다섯 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper5["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper5["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper5["J3"], 30, -1)
    await PTP(cf.new_pick_dripper5["J4"], 70, -1)

async def new_pick_dripper6():
    print("여섯 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper6["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper6["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper6["J3"], 30, -1)
    await PTP(cf.new_pick_dripper6["J4"], 70, -1)
    await PTP(cf.new_pick_dripper6["J5"], 70, -1)

async def new_pick_dripper7():
    print("일곱 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper7["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper7["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper7["J3"], 30, -1)
    await PTP(cf.new_pick_dripper7["J4"], 70, -1)
    await PTP(cf.new_pick_dripper7["J5"], 70, -1)

async def new_pick_dripper8():
    print("여덟 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper8["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper8["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper8["J3"], 30, -1)
    await PTP(cf.new_pick_dripper8["J4"], 70, -1)

async def new_pick_dripper9():
    print("아홉 번째 드리퍼를 집습니다.")
    await PTP(cf.new_pick_dripper9["J1"], 100, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper9["J2"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper9["J3"], 30, -1)
    await PTP(cf.new_pick_dripper9["J4"], 70, -1)
    await PTP(cf.new_pick_dripper9["J5"], 70, -1)

async def new_ready_for_set_1st_floor_dripper():
    print("1층 드리퍼 준비 완료.")
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J1"], 100, -1)
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J2"], 100, -1)
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J3"], 100, -1)
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J4"], 100, -1)
    
async def new_ready_for_set_234_floor_dripper():
    print("2-4층 드리퍼 준비 완료.")
    await PTP(cf.new_ready_for_set_234_floor_dripper["J1"], 100, -1)
    await PTP(cf.new_ready_for_set_234_floor_dripper["J2"], 100, -1)
    await PTP(cf.new_ready_for_set_234_floor_dripper["J3"], 100, -1)


async def back_setready_1st_floor_dripper():
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J1"], 100, -1)
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J2"], 100, -1)
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J3"], 100, -1)
    await PTP(cf.new_ready_for_set_1st_floor_dripper["J4"], 100, -1)

async def back_setready_234_floor_dripper():
    await PTP(cf.new_ready_for_set_234_floor_dripper["J1"], 100, -1)
    await PTP(cf.new_ready_for_set_234_floor_dripper["J2"], 100, -1)
    await PTP(cf.new_ready_for_set_234_floor_dripper["J3"], 100, -1)

async def back_pick_dripper1():    
    await PTP(cf.new_pick_dripper1["J5"], 100, -1)
    await PTP(cf.new_pick_dripper1["J4"], 70, -1)
    await PTP(cf.new_pick_dripper1["J3"], 70, -1)
    await PTP(cf.new_pick_dripper1["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper1["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper2():    
    await PTP(cf.new_pick_dripper2["J4"], 100, -1)
    await PTP(cf.new_pick_dripper2["J3"], 70, -1)
    await PTP(cf.new_pick_dripper2["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper2["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper3():  
    await PTP(cf.new_pick_dripper3["J5"], 100, -1)
    await PTP(cf.new_pick_dripper3["J4"], 70, -1)
    await PTP(cf.new_pick_dripper3["J3"], 70, -1)
    await PTP(cf.new_pick_dripper3["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper3["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper4():   
    await PTP(cf.new_pick_dripper4["J5"], 100, -1)
    await PTP(cf.new_pick_dripper4["J4"], 70, -1)
    await PTP(cf.new_pick_dripper4["J3"], 70, -1)
    await PTP(cf.new_pick_dripper4["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper4["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper5():
    await PTP(cf.new_pick_dripper5["J4"], 100, -1)
    await PTP(cf.new_pick_dripper5["J3"], 70, -1)
    await PTP(cf.new_pick_dripper5["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper5["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper6():
    await PTP(cf.new_pick_dripper6["J5"], 100, -1)
    await PTP(cf.new_pick_dripper6["J4"], 70, -1)
    await PTP(cf.new_pick_dripper6["J3"], 70, -1)
    await PTP(cf.new_pick_dripper6["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper6["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper7():
    await PTP(cf.new_pick_dripper7["J5"], 100, -1)
    await PTP(cf.new_pick_dripper7["J4"], 70, -1)
    await PTP(cf.new_pick_dripper7["J3"], 70, -1)
    await PTP(cf.new_pick_dripper7["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper7["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper8():
    await PTP(cf.new_pick_dripper8["J4"], 100, -1)
    await PTP(cf.new_pick_dripper8["J3"], 70, -1)
    await PTP(cf.new_pick_dripper8["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper8["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_pick_dripper9():
    await PTP(cf.new_pick_dripper9["J5"], 100, -1)
    await PTP(cf.new_pick_dripper9["J4"], 70, -1)
    await PTP(cf.new_pick_dripper9["J3"], 70, -1)
    await PTP(cf.new_pick_dripper9["J2"], 30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.new_pick_dripper9["J1"], 30, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def new_set_dripper_1st_pos():
    print("첫 번째 위치에 드리퍼를 놓습니다.")    
    await PTP(cf.new_set_dripper_1st_pos["J1"], 100, -1)
    await PTP(cf.new_set_dripper_1st_pos["J2"], 70, -1)
    await PTP(cf.new_set_dripper_1st_pos["J3"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_set_dripper_1st_pos["J4"], 30, -1)

async def new_set_dripper_2nd_pos():
    print("두 번째 위치에 드리퍼를 놓습니다.")
    await PTP(cf.new_set_dripper_2nd_pos["J1"], 100, -1)
    await PTP(cf.new_set_dripper_2nd_pos["J2"], 70, -1)
    await PTP(cf.new_set_dripper_2nd_pos["J3"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_set_dripper_2nd_pos["J4"], 30, -1)
    
async def new_set_dripper_3rd_pos():
    print("세 번째 위치에 드리퍼를 놓습니다.")
    await PTP(cf.new_set_dripper_3rd_pos["J1"], 100, -1)
    await PTP(cf.new_set_dripper_3rd_pos["J2"], 70, -1)
    await PTP(cf.new_set_dripper_3rd_pos["J3"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_set_dripper_3rd_pos["J4"], 30, -1)
    await PTP(cf.new_set_dripper_3rd_pos["J5"], 100, -1)

async def new_preparing_pick_dripper():
    print("드리퍼를 집기 위한 준비를 합니다.")
    print(cf.new_preparing_pick_dripper["J1"], 100, -1)
    await PTP(cf.new_preparing_pick_dripper["J1"], 100, -1)

async def back_dripper_1st_pos():
    await PTP(cf.set_dripper_back_ready_pos["J1"], 100, -1)
    
    await PTP(cf.new_set_dripper_1st_pos["J4"], 70, -1)
    await PTP(cf.new_set_dripper_1st_pos["J3"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_set_dripper_1st_pos["J2"], 70, -1)
    await PTP(cf.new_set_dripper_1st_pos["J1"], 70, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_dripper_2nd_pos():
    await PTP(cf.set_dripper_back_ready_pos["J1"], 100, -1)
    
    await PTP(cf.new_set_dripper_2nd_pos["J4"], 70, -1)
    await PTP(cf.new_set_dripper_2nd_pos["J3"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_set_dripper_2nd_pos["J2"], 70, -1)
    await PTP(cf.new_set_dripper_2nd_pos["J1"], 70, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)

async def back_dripper_3rd_pos():
    await PTP(cf.set_dripper_back_ready_pos["J1"], 100, -1)
    
    await PTP(cf.new_set_dripper_3rd_pos["J5"], 70, -1)
    await PTP(cf.new_set_dripper_3rd_pos["J4"], 70, -1)
    await PTP(cf.new_set_dripper_3rd_pos["J3"], 30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_set_dripper_3rd_pos["J2"], 70, -1)
    await PTP(cf.new_set_dripper_3rd_pos["J1"], 70, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 70, -1)


async def shaking_dripper1():
    print("1번 드리퍼의 원두를 평탄화합니다.")
    await PTP(cf.new_shaking_dripper1["J1"], 50, -1)
    await PTP(cf.new_shaking_dripper1["J2"], 50, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper1["J3"], 100, -1)
    await PTP(cf.new_shaking_dripper1["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J7"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J7"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J3"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J2"], 100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper1["J1"], 50, -1)

async def shaking_dripper2():
    print("2번 드리퍼의 원두를 평탄화합니다.")
    await PTP(cf.new_shaking_dripper2["J1"], 50, -1)
    await PTP(cf.new_shaking_dripper2["J2"], 50, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper2["J3"], 100, -1)
    await PTP(cf.new_shaking_dripper2["J4"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J4"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J3"], 100, -1)
    await PTP(cf.new_shaking_dripper2["J2"], 100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper2["J1"], 50, -1)

async def shaking_dripper3():
    print("3번 드리퍼의 원두를 평탄화합니다.")
    await PTP(cf.new_shaking_dripper3["J1"], 50, -1)
    await PTP(cf.new_shaking_dripper3["J2"], 50, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper3["J3"], 100, -1)
    await PTP(cf.new_shaking_dripper3["J4"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J4"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J3"], 100, -1)
    await PTP(cf.new_shaking_dripper3["J2"], 100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper3["J1"], 50, -1)

async def standard_spiral1(SPEED, ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0, ext):
    repos = None
    print("1번 드리퍼에 Spiral")
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [pa0, 0.0, 0.0, 30.0, 0.0, 0.0]

    await PTP(cf.pouring_water_dripper1["J1"], 60, -1)
    repos = cf.pouring_water_dripper1["J2"]
    repos[5] = ang
    repos[4] = ang_sub1
    repos[3] = ang_sub2
    repos[2] = ang_sub3
    repos[1] = ang_sub4
    repos[0] = ang_sub5
    print("Spiral 좌표 : ", repos, "pa0 : ", pa0, "speed : ", SPEED)
    await PTP(repos, 20, -1)
    print("Spiral... ")
    await newSPIRAL(repos, SPEED, Pa1, DP1)
    await PTP(cf.pouring_water_dripper1["J1"], 90, -1)
    await asyncio.sleep(ext)

async def spiral1():
    for i in range(1, 6):
        pa0 = [0.0, 1.8, 1.6, 1.8, 1.6, 1.8]
        spd = [0, 90, 100, 90, 100, 90]
        ext = [0, 45, 25, 25, 18, 1]
        ang = list(cf.pouring_water_dripper1.values())[i][5]
        ang_sub1 = list(cf.pouring_water_dripper1.values())[i][4]
        ang_sub2 = list(cf.pouring_water_dripper1.values())[i][3]
        ang_sub3 = list(cf.pouring_water_dripper1.values())[i][2]
        ang_sub4 = list(cf.pouring_water_dripper1.values())[i][1]
        ang_sub5 = list(cf.pouring_water_dripper1.values())[i][0]

        await standard_spiral1(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i])


async def standard_pour1(ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5): # j6, j5, j4, j3
    repos = None
    print("1번 드리퍼에 Pour")
    await PTP(cf.test_spiral1["J1"], 100, -1)
    repos = cf.test_spiral1["J2"]
    repos[5] = repos[5] + float(ang)
    repos[4] = repos[4] + float(ang_sub1)
    repos[3] = repos[3] + float(ang_sub2)
    repos[2] = repos[2] + float(ang_sub3)
    repos[1] = repos[1] + float(ang_sub4)
    repos[0] = repos[0] + float(ang_sub5)
    await PTP(repos, 20, -1)
    await asyncio.sleep(13)
    await PTP(cf.test_spiral1["J1"], 100, -1)

# async def standard_spiral2(SPEED, ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0, ext):
#     repos = None
#     print("2번 드리퍼에 Spiral")
#     DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
#     Pa1 = [pa0, 0.0, 0.0, 30.0, 0.0, 0.0]

#     await PTP(cf.pouring_water_dripper2["J1"], 30, -1)
#     repos = cf.pouring_water_dripper2["J2"]
#     repos[5] = repos[5] + ang
#     repos[4] = repos[4] + ang_sub1
#     repos[3] = repos[3] + ang_sub2
#     repos[2] = repos[2] + ang_sub3
#     repos[1] = repos[1] + ang_sub4
#     repos[0] = repos[0] + ang_sub5

#     print("Spiral 좌표 : ", repos, "pa0 : ", pa0, "speed : ", SPEED)
#     await PTP(repos, 20, -1)
#     print("Spiral... ")
#     await newSPIRAL(repos, SPEED, Pa1, DP1)
#     await PTP(cf.pouring_water_dripper2["J1"], 100, -1)
#     await asyncio.sleep(ext)

async def standard_spiral2(SPEED, ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0, ext):
    repos = None
    print("2번 드리퍼에 Spiral")
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [pa0, 0.0, 0.0, 30.0, 0.0, 0.0]

    await PTP(cf.pouring_water_dripper2["J1"], 60, -1)
    repos = cf.pouring_water_dripper2["J2"]
    repos[5] = ang
    repos[4] = ang_sub1
    repos[3] = ang_sub2
    repos[2] = ang_sub3
    repos[1] = ang_sub4
    repos[0] = ang_sub5
    print("Spiral 좌표 : ", repos, "pa0 : ", pa0, "speed : ", SPEED)
    await PTP(repos, 20, -1)
    print("Spiral... ")
    await newSPIRAL(repos, SPEED, Pa1, DP1)
    await PTP(cf.pouring_water_dripper2["J1"], 90, -1)
    await asyncio.sleep(ext)

# async def spiral2():
#      for i in range(0, 5):
#             pa0 = [1.8, 1.8, 1.8, 1.8, 1.8]
#             spd = [65, 90, 65, 90, 75]
#             ext = [15, 15, 15, 15, 15]

#             if i % 2 == 1 :
#                 ang = 5
#                 ang_sub1 = 1.58
#                 ang_sub2 = -0.568
#                 ang_sub3 = -0.773
#                 ang_sub4 = 1.428
#                 ang_sub5 = 1.555
#             else :
#                 ang = 0
#                 ang_sub1 = 0
#                 ang_sub2 = 0
#                 ang_sub3 = 0
#                 ang_sub4 = 0
#                 ang_sub5 = 0

#             standard_spiral2(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i])
    
async def spiral2():
    for i in range(1, 6):
        pa0 = [0.0, 1.8, 1.6, 1.8, 1.6, 1.8]
        spd = [0, 90, 100, 90, 100, 90]
        ext = [0, 45, 25, 25, 18, 1]
        ang = list(cf.pouring_water_dripper2.values())[i][5]
        ang_sub1 = list(cf.pouring_water_dripper2.values())[i][4]
        ang_sub2 = list(cf.pouring_water_dripper2.values())[i][3]
        ang_sub3 = list(cf.pouring_water_dripper2.values())[i][2]
        ang_sub4 = list(cf.pouring_water_dripper2.values())[i][1]
        ang_sub5 = list(cf.pouring_water_dripper2.values())[i][0]

        await standard_spiral2(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i])


async def standard_pour2(ang, ang_sub1, ang_sub2, ang_sub3):
    repos = None
    print("2번 드리퍼에 Pour")
    await PTP(cf.spiral2["J1"], 100, -1)
    repos = cf.spiral2["J2"]
    repos[5] = repos[5] + float(ang)
    repos[4] = repos[4] + float(ang_sub1)
    repos[3] = repos[3] + float(ang_sub2)
    repos[2] = repos[2] + float(ang_sub3)
    await PTP(repos, 20, -1)
    await asyncio.sleep(13)
    await PTP(cf.spiral2["J1"], 100, -1)
    
async def standard_spiral3(SPEED, ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0, ext):
    repos = None
    print("2번 드리퍼에 Spiral")
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [pa0, 0.0, 0.0, 30.0, 0.0, 0.0]

    await PTP(cf.pouring_water_dripper3["J1"], 60, -1)
    repos = cf.pouring_water_dripper3["J2"]
    repos[5] = ang
    repos[4] = ang_sub1
    repos[3] = ang_sub2
    repos[2] = ang_sub3
    repos[1] = ang_sub4
    repos[0] = ang_sub5
    print("Spiral 좌표 : ", repos, "pa0 : ", pa0, "speed : ", SPEED)
    await PTP(repos, 20, -1)
    print("Spiral... ")
    await newSPIRAL(repos, SPEED, Pa1, DP1)
    await PTP(cf.pouring_water_dripper3["J1"], 90, -1)
    await asyncio.sleep(ext)

async def spiral3():
    for i in range(1, 6):
        pa0 = [0.0, 1.8, 1.6, 1.8, 1.6, 1.8]
        spd = [0, 90, 100, 90, 100, 90]
        ext = [0, 45, 25, 25, 18, 1]
        ang = list(cf.pouring_water_dripper3.values())[i][5]
        ang_sub1 = list(cf.pouring_water_dripper3.values())[i][4]
        ang_sub2 = list(cf.pouring_water_dripper3.values())[i][3]
        ang_sub3 = list(cf.pouring_water_dripper3.values())[i][2]
        ang_sub4 = list(cf.pouring_water_dripper3.values())[i][1]
        ang_sub5 = list(cf.pouring_water_dripper3.values())[i][0]

        await standard_spiral3(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i])

async def standard_pour3(ang, ang_sub1, ang_sub2, ang_sub3):
    repos = None
    print("3번 드리퍼에 Pour")
    await PTP(cf.spiral3["J1"], 100, -1)
    repos = cf.spiral3["J2"]
    repos[5] = repos[5] + float(ang)
    repos[4] = repos[4] + float(ang_sub1)
    repos[3] = repos[3] + float(ang_sub2)
    repos[2] = repos[2] + float(ang_sub3)
    await PTP(repos, 20, -1)
    await asyncio.sleep(13)
    await PTP(cf.spiral3["J1"], 100, -1)


async def delivery1():
    robot.SetSpeed(60)
    await PTP(cf.delivery_home["J1"], 100, -1)
    await PTP(cf.delivery_cup1["J1"], 100, -1)
    await PTP(cf.delivery_cup1["J2"], 100, -1)
    await PTP(cf.delivery_cup1["J3"], 100, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.delivery_cup1["J4"], 100, -1)
    await PTP(cf.delivery_cup1["J5"], 100, -1)
    await PTP(cf.delivery_cup1["J6"], 100, -1)
    await PTP(cf.delivery_cup1["J7"], 100, -1)
    await PTP(cf.delivery_cup1["J8"], 100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.delivery_cup1["J7"], 100, -1)
    await PTP(cf.delivery_cup1["J6"], 100, -1)
    await PTP(cf.delivery_home["J1"], 100, -1)

async def delivery2():    
    robot.SetSpeed(60)
    await PTP(cf.delivery_home["J1"], 100, -1)
    await PTP(cf.delivery_cup2["J1"], 100, -1)
    await PTP(cf.delivery_cup2["J2"], 100, -1)
    await PTP(cf.delivery_cup2["J3"], 100, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.delivery_cup2["J4"], 100, -1)
    await PTP(cf.delivery_cup2["J5"], 100, -1)
    await PTP(cf.delivery_cup2["J6"], 100, -1)
    await PTP(cf.delivery_cup2["J7"], 100, -1)
    await PTP(cf.delivery_cup2["J8"], 100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.delivery_cup2["J7"], 100, -1)
    await PTP(cf.delivery_cup2["J6"], 100, -1)
    await PTP(cf.delivery_home["J1"], 100, -1)

async def delivery3():
    robot.SetSpeed(60)
    await PTP(cf.delivery_home["J1"], 100, -1)
    await PTP(cf.delivery_cup3["J1"], 100, -1)
    await PTP(cf.delivery_cup3["J2"], 100, -1)
    await PTP(cf.delivery_cup3["J3"], 100, -1)
    await movegripper(1, 0, 50, 50, 10000, 0)
    await PTP(cf.delivery_cup3["J4"], 100, -1)
    await PTP(cf.delivery_cup3["J5"], 100, -1)
    await PTP(cf.delivery_cup3["J6"], 100, -1)
    await PTP(cf.delivery_cup3["J7"], 100, -1)
    await PTP(cf.delivery_cup3["J8"], 100, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.delivery_cup3["J7"], 100, -1)
    await PTP(cf.delivery_cup3["J6"], 100, -1)
    await PTP(cf.delivery_home["J1"], 100, -1)



async def hello_drip():
    await PTP(cf.hello_drip_pos["J0"], 100, -1)
    await PTP(cf.hello_drip_pos["J1"], 100, -1)
    await PTP(cf.hello_drip_pos["J0"], 100, -1)
    await PTP(cf.hello_drip_pos["J1"], 100, -1)
    await PTP(cf.hello_drip_pos["J0"], 100, -1)
    await PTP(cf.hello_drip_pos["J1"], 100, -1)
    await PTP(cf.home_point["J"], 70, -1)


async def beancup_pick(cup_point):
	if cup_point == 1:
	    await beancup_pick1()
	elif cup_point == 2:
	    await beancup_pick2()
	elif cup_point == 3:
	    await beancup_pick3()

async def beancup_back(cup_point):
	if cup_point == 1:
	    await beancup_back1()
	elif cup_point == 2:
	    await beancup_back2()
	elif cup_point == 3:
	    await beancup_back3()

async def beancup_dropbean(drip_point):
	if drip_point == 1:
	    await beancup_dropbean1()
	elif drip_point == 2:
	    await beancup_dropbean2()
	elif drip_point == 3:
	    await beancup_dropbean3()

async def shaking_dripper(drip_point):
	if drip_point == 1:
	    await shaking_dripper1()
	elif drip_point == 2:
	    await shaking_dripper2()
	elif drip_point == 3:
    	    await shaking_dripper3()

async def spiral_dripper(drip_point):
	if drip_point == 1:
	    await spiral1()
	elif drip_point == 2:
	    await spiral2()
	elif drip_point == 3:
	    await spiral3()

async def delivery(drip_point):
        if drip_point == 1:
            await delivery1()
        elif drip_point == 2:
            await delivery2()
        elif drip_point == 3:
            await delivery3()

