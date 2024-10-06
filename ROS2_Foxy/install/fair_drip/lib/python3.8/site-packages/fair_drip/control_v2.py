import os
import numpy as np
import pandas as pd
import time

import asyncio

import fair_drip.conf_file as cf
import fair_drip.frrpc as frrpc
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

def transform_pose(joint):
    pose = robot.GetForwardKin(joint)
    cartesian_pose = [pose[1], pose[2], pose[3], pose[4], pose[5], pose[6]]
    return cartesian_pose

def transform_joint(pose):
    joint = robot.GetInverseKin(0, pose, -1)
    joint_pose = [joint[1], joint[2], joint[3], joint[4], joint[5], joint[6]]
    return joint_pose

async def PTP( J=None, SPEED=70.0, BLEND=-1, P=None):

        SPEED = float(SPEED)
        BLEND = float(BLEND)
        if P is None:
            P = transform_pose(J)
        if J is None:
            J = transform_joint(P)
        robot.MoveJ(J, P, 0, 0, SPEED, 100.0, BLEND, EP, -1.0, 0, DP)

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
    await PTP(cf.new_pick_fullwater_kettle["J94"], 70, -1)
    await PTP(cf.new_pick_fullwater_kettle["J95"], 50, -1)
    await PTP(cf.new_pick_fullwater_kettle["J96"], 30, -1)
    await PTP(cf.new_pick_fullwater_kettle["J97"], 30, -1)
    await movegripper(1, 18, 50, 50, 10000, 0)
    await PTP(cf.new_pick_fullwater_kettle["J98"], 30, -1)
    await PTP(cf.new_pick_fullwater_kettle["J99"], 70, -1)
    await PTP(cf.new_pick_fullwater_kettle["J100"], 100, -1)

async def kettle_back():
    await PTP(cf.new_pick_fullwater_kettle["J100"], 100, -1)
    await PTP(cf.new_pick_fullwater_kettle["J99"], 100, -1)
    await PTP(cf.new_pick_fullwater_kettle["J98"], 70, -1)
    await PTP(cf.new_pick_fullwater_kettle["J97"], 30, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_pick_fullwater_kettle["J96"], 30, -1)
    await PTP(cf.new_pick_fullwater_kettle["J95"], 70, -1)
    await PTP(cf.new_pick_fullwater_kettle["J94"], 100, -1)
    await PTP(cf.new_pick_fullwater_kettle["J93"], 100, -1)
    await PTP(cf.new_pick_fullwater_kettle["J92"], 100, -1)
    await PTP(cf.new_pick_fullwater_kettle["J91"], 100, -1)
        
async def pouring_water():
    await PTP(cf.pouring_water["J0"], 70, -1)
    await PTP(cf.pouring_water["J1"], 30,-1)
    await PTP(cf.pouring_water["J2"], 20,-1) 
    await PTP(cf.pouring_water["J3"], 20,-1) 
    time.sleep(3)
    await PTP(cf.pouring_water["J1"], 10,-1)

async def beancup_pick():
    await movegripper(1, 80, 50, 50, 10000, 0)
    
    await PTP(cf.pick_bean_cup['J1'],100, -1)
    await PTP(cf.pick_bean_cup['J2'],70, -1)
    await PTP(cf.pick_bean_cup['J3'],30, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup['J4'],30, -1)
    await PTP(cf.pick_bean_cup['J5'],100, -1)

async def beancup_back():
    await PTP(cf.pick_bean_cup['J1'],100, -1)
    await PTP(cf.pick_bean_cup['J4'],70, -1)
    await PTP(cf.pick_bean_cup['J3'],30, -1)
    await movegripper(1, 80, 50, 50, 10000, 0)
    await PTP(cf.pick_bean_cup['J2'],30, -1)
    await PTP(cf.pick_bean_cup['J1'],100, -1)

async def beancup_grinding_bean_in():
    await PTP(cf.grinding_coffee_bean['J1'],100, -1)

async def beancup_grinding_bean_out():
    await PTP(cf.grinding_coffee_bean['J2'],100, -1)

async def beancup_dropbean_ready():
    await PTP(cf.moving_coffee_bean['J1'], 100, -1)
    await PTP(cf.moving_coffee_bean['J2'], 100, -1)
    await PTP(cf.moving_coffee_bean['J3'], 100, -1)

async def beancup_dropbean_1():
    await PTP(cf.set_coffee_bean_dripper1['J1'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper1['J1'], 100, -1)
    
async def beancup_dropbean_2():        
    await PTP(cf.set_coffee_bean_dripper2['J1'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper2['J1'], 100, -1)

async def beancup_dropbean_3():
    await PTP(cf.set_coffee_bean_dripper3['J1'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J3'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J2'], 100, -1)
    await PTP(cf.set_coffee_bean_dripper3['J1'], 100, -1)

async def beancup_dropbean_end():
    await PTP(cf.moving_coffee_bean['J3'], 100, -1)
    await PTP(cf.moving_coffee_bean['J2'], 100, -1)
    
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
    await PTP(cf.new_preparing_pick_dripper["J1"], 100, -1)
    await PTP(cf.new_preparing_pick_dripper["J2"], 100, -1)

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
    await PTP(cf.new_shaking_dripper1["J1"], 100, -1)
    await PTP(cf.new_shaking_dripper1["J2"], 100, -1)
    await PTP(cf.new_shaking_dripper1["J3"], 100, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper1["J4"], 100, -1)
    await PTP(cf.new_shaking_dripper1["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper1["J4"], 100, 100)
    await PTP(cf.new_shaking_dripper1["J3"], 20, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper1["J2"], 100, -1)
    await PTP(cf.new_shaking_dripper1["J1"], 100, -1)

async def shaking_dripper2():
    print("1번 드리퍼의 원두를 평탄화합니다.")
    await PTP(cf.new_shaking_dripper2["J1"], 100, -1)
    await PTP(cf.new_shaking_dripper2["J2"], 100, -1)
    await PTP(cf.new_shaking_dripper2["J3"], 100, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper2["J4"], 100, -1)
    await PTP(cf.new_shaking_dripper2["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper2["J4"], 100, 100)
    await PTP(cf.new_shaking_dripper2["J3"], 20, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper2["J2"], 100, -1)
    await PTP(cf.new_shaking_dripper2["J1"], 100, -1)

async def shaking_dripper3():
    print("1번 드리퍼의 원두를 평탄화합니다.")
    await PTP(cf.new_shaking_dripper3["J1"], 100, -1)
    await PTP(cf.new_shaking_dripper3["J2"], 100, -1)
    await PTP(cf.new_shaking_dripper3["J3"], 100, -1)
    await PTP(cf.new_shaking_dripper3["J4"], 100, -1)
    await movegripper(1, 15, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper3["J5"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J7"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J7"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J7"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J7"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J6"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J7"], 100, 500)
    await PTP(cf.new_shaking_dripper3["J5"], 100, 100)
    await PTP(cf.new_shaking_dripper3["J4"], 20, -1)
    await movegripper(1, 100, 50, 50, 10000, 0)
    await PTP(cf.new_shaking_dripper3["J3"], 20, -1)
    await PTP(cf.new_shaking_dripper3["J2"], 100, -1)
    await PTP(cf.new_shaking_dripper3["J1"], 100, -1)

async def standard_spiral1(SPEED, ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5):
    repos = None

    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [2.0, 0.0, 0.0, 20.0, 20.0, 0.0]
    
    await PTP(cf.spiral_1["J1"], 100, -1)
    repos = cf.spiral_1["J2"]

    repos[5] = repos[5] + float(ang)
    repos[4] = repos[4] + float(ang_sub1)
    repos[3] = repos[3] + float(ang_sub2)
    repos[2] = repos[2] + float(ang_sub3)
    repos[1] = repos[1] + float(ang_sub4)
    repos[0] = repos[0] + float(ang_sub5)

    await PTP(repos, 20, -1)
    await newSPIRAL(repos, SPEED, Pa1, DP1)
    await PTP(cf.spiral_1["J1"], 100, -1)

    del repos

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

async def standard_spiral2(SPEED, ang, ang_sub1, ang_sub2, ang_sub3):
    repos = None
    print("2번 드리퍼에 Spiral")
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [2.0, 0.0, 0.0, 20.0, 20.0, 0.0]

    await PTP(cf.spiral2["J1"], 100, -1)
    repos = cf.spiral2["J2"]
    repos[5] = repos[5] + float(ang)
    repos[4] = repos[4] + float(ang_sub1)
    repos[3] = repos[3] + float(ang_sub2)
    repos[2] = repos[2] + float(ang_sub3)
    print("Spiral 좌표 : ", repos)
    await PTP(repos, 20, -1)
    await newSPIRAL(repos, SPEED, Pa1, DP1)
    await PTP(cf.spiral2["J1"], 100, -1)

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
    
async def standard_spiral3(SPEED, ang, ang_sub1, ang_sub2, ang_sub3):
    repos = None
    print("3번 드리퍼에 Spiral")
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [2.0, 0.0, 0.0, 20.0, 20.0, 0.0]

    await PTP(cf.spiral3["J1"], 100, -1)
    repos = cf.spiral3["J2"]
    repos[5] = repos[5] + float(ang)
    repos[4] = repos[4] + float(ang_sub1)
    repos[3] = repos[3] + float(ang_sub2)
    repos[2] = repos[2] + float(ang_sub3)
    print("Spiral 좌표 : ", repos)
    await PTP(repos, 20, -1)
    await newSPIRAL(repos, SPEED, Pa1, DP1)
    await PTP(cf.test_spiral3["J1"], 100, -1)

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

async def hello_drip():
    await PTP(cf.hello_drip_pos["J0"], 100, -1)
    await PTP(cf.hello_drip_pos["J1"], 100, -1)
    await PTP(cf.hello_drip_pos["J0"], 100, -1)
    await PTP(cf.hello_drip_pos["J1"], 100, -1)
    await PTP(cf.hello_drip_pos["J0"], 100, -1)
    await PTP(cf.hello_drip_pos["J1"], 100, -1)
    await PTP(cf.home_point["J"], 70, -1)
