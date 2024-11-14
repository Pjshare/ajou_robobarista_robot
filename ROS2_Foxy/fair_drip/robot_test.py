
import frrpc
import conf_file as cf
import time
from fair_drip import control_v2
import asyncio

## Robot info
ROBOT_IP = "192.168.58.2" 
robot = frrpc.RPC(ROBOT_IP)

EP=[0.000, 0.000, 0.000, 0.000]
DP=[1.000, 1.000, 1.000, 1.000, 1.000, 1.000]
EP2=[0.000,0.000,0.000,0.000]

def actionHome():
    robot_main = frrpc.RPC(ROBOT_IP)
    # control = RobotControl(robot_main)
    speed = 80
    robot.SetSpeed(speed)
    SPEED = float(100)
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [2.0, 0.0, 0.0, 20.0, 20.0, 0.0]
    pos0 = [1.327,-130.671,139.899,-101.789,87.985,-90.735] #89.265
    PTP(pos0, 100, -1)

def action00():
    robot_main = frrpc.RPC(ROBOT_IP)
    # control = RobotControl(robot_main)
    speed = 30
    robot.SetSpeed(speed)
    SPEED = float(100)
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [2.0, 0.0, 0.0, 20.0, 20.0, 0.0]
    pos1 = [14.485, -93.489, 110.195, -103.067, 57.88, -90.736] #89.264
    pos2 = [-14.485, -93.489, 110.195, -103.067, 113.866, -90.736]#89.264
    PTP(pos1, 100, -1)
    PTP(pos2, 100, -1)

def newSPIRAL(J1, SPEED, Pa, DP):
    P1 = transform_pose(J1)
    robot.NewSpiral(J1, P1, 0, 0, float(SPEED), 0.0, EP2, 50.0, 2, DP, Pa)

    while True:
        motion_state = robot.GetRobotMotionDone()
        if motion_state[1] == 1:
            break
        # print("스파이럴 대기")
        time.sleep(0.1)
        
def movegripper(index, pos, vel, force, max_time, last_arg=0):
    robot.MoveGripper(index, pos, vel, force, max_time, last_arg)
    start_time = time.time()
    while time.time() - start_time < 1.0:  
        gripper_state = robot.GetGripperMotionDone()
        if gripper_state[2] == 1:  
            break
        print("Gripper 동작 대기 중...")
        time.sleep(0.1)

def PTP(J=None, SPEED=70.0, BLEND=-1, P=None):

            SPEED = float(SPEED)
            BLEND = float(BLEND)
            if P is None:
                P = transform_pose(J)
            if J is None:
                J = transform_joint(P)
            robot.MoveJ(J, P, 0, 0, SPEED, 100.0, BLEND, EP, -1.0, 0, DP)

def transform_pose(joint):
    pose = robot.GetForwardKin(joint)
    cartesian_pose = [pose[1], pose[2], pose[3], pose[4], pose[5], pose[6]]
    return cartesian_pose

def transform_joint(pose):
    joint = robot.GetInverseKin(0, pose, -1)
    joint_pose = [joint[1], joint[2], joint[3], joint[4], joint[5], joint[6]]
    return joint_pose

if __name__ == "__main__":

    # actionHome()
    # action00()
    # asyncio.run(control_v2.beancup_pick1())
    # # asyncio.run(control_v2.beancup_pick2())
    # # asyncio.run(control_v2.beancup_pick3())
    # asyncio.run(control_v2.beancup_dropbean_ready())
    # asyncio.run(control_v2.beancup_dropbean_1())
    # # asyncio.run(control_v2.beancup_dropbean_2())
    # # asyncio.run(control_v2.beancup_dropbean_3())
    # asyncio.run(control_v2.beancup_back1())
    # # asyncio.run(control_v2.beancup_back2())
    # # asyncio.run(control_v2.beancup_back3())
    # asyncio.run(control_v2.new_preparing_pick_dripper())
    asyncio.run(control_v2.shaking_dripper1())
    # asyncio.run(control_v2.new_preparing_pick_dripper())
    # # asyncio.run(control_v2.shaking_dripper2())
    # # asyncio.run(control_v2.new_preparing_pick_dripper())
    # # asyncio.run(control_v2.shaking_dripper3())
    # # asyncio.run(control_v2.new_preparing_pick_dripper())

    # asyncio.run(control_v2.kettle_pick())
    # asyncio.run(control_v2.pouring_water())
    # asyncio.run(control_v2.pouring_water_home())
    
    # robot.SetSpeed(100)


    # # 첫번째 드리퍼에 spiral 
    # # for i in range(1, 6):
    # #     pa0 = [0.0, 1.8, 1.6, 2.0, 1.6, 2.0]
    # #     spd = [0, 80, 90, 80, 90, 80]
    # #     ext = [0, 45, 25, 25, 18, 1]
    # #     ang = list(cf.pouring_water_dripper1.values())[i][5]
    # #     ang_sub1 = list(cf.pouring_water_dripper1.values())[i][4]
    # #     ang_sub2 = list(cf.pouring_water_dripper1.values())[i][3]
    # #     ang_sub3 = list(cf.pouring_water_dripper1.values())[i][2]
    # #     ang_sub4 = list(cf.pouring_water_dripper1.values())[i][1]
    # #     ang_sub5 = list(cf.pouring_water_dripper1.values())[i][0]

    # #     asyncio.run(control_v2.standard_spiral1(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i]))
    # #     if i==5:
    # #         print("over")

    # # 두번째 드리퍼에 spiral 
    # for i in range(0, 5):
    #         pa0 = [1.8, 1.8, 1.8, 1.8, 1.8]
    #         spd = [65, 90, 65, 90, 75]
    #         ext = [15, 15, 15, 15, 15]

    #         if i % 2 == 1 :
    #             ang = 5
    #             ang_sub1 = 1.58
    #             ang_sub2 = -0.568
    #             ang_sub3 = -0.773
    #             ang_sub4 = 1.428
    #             ang_sub5 = 1.555
    #         else :
    #             ang = 0
    #             ang_sub1 = 0
    #             ang_sub2 = 0
    #             ang_sub3 = 0
    #             ang_sub4 = 0
    #             ang_sub5 = 0

    #         asyncio.run(control_v2.standard_spiral2(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i]))
    #         if i==5:
    #             print("over")

    # asyncio.run(control_v2.kettle_back())












    # for i in range(10):
    #     actionHome()
    #     for i in range(4):
    #         action00()
        