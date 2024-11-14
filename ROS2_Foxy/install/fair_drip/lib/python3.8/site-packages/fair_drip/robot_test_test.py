
import frrpc
import conf_file as cf
import time
import control_v2 as cv
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
    movegripper(1, 100, 50, 50, 10000, 0)
    SPEED = float(100)
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [2.0, 0.0, 0.0, 20.0, 20.0, 0.0]
    pos0 = [1.324,-130.612,139.911,-101.797,93.759,-90.000] #89.265
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
    # asyncio.run(cv.beancup_pick1())
    # asyncio.run(cv.beancup_pick2())
    # # asyncio.run(cv.beancup_pick3())
    # asyncio.run(cv.beancup_dropbean_ready())
    # # asyncio.run(cv.beancup_dropbean1())
    # asyncio.run(cv.beancup_dropbean2())
    # # asyncio.run(cv.beancup_dropbean3())
    # asyncio.run(cv.beancup_back1())
    # asyncio.run(cv.beancup_back2())
    # # asyncio.run(cv.beancup_back3())
    # asyncio.run(cv.new_preparing_pick_dripper())
    # asyncio.run(cv.shaking_dripper1())
    # asyncio.run(cv.new_preparing_pick_dripper())
    # asyncio.run(cv.shaking_dripper2())
    asyncio.run(cv.new_preparing_pick_dripper())
    asyncio.run(cv.shaking_dripper3())
    # asyncio.run(cv.new_preparing_pick_dripper())

    # asyncio.run(cv.kettle_pick())
    # asyncio.run(cv.pouring_water())
    # asyncio.run(cv.pouring_water_home())
    


    # # 첫번째 드리퍼에 spiral 
    # # for i in range(1, 6):
    # #     pa0 = [0.0, 1.8, 1.6, 1.8, 1.6, 1.8]
    # #     spd = [0, 90, 100, 90, 100, 90]
    # #     ext = [0, 45, 25, 25, 18, 1]
    # #     ang = list(cf.pouring_water_dripper1.values())[i][5]
    # #     ang_sub1 = list(cf.pouring_water_dripper1.values())[i][4]
    # #     ang_sub2 = list(cf.pouring_water_dripper1.values())[i][3]
    # #     ang_sub3 = list(cf.pouring_water_dripper1.values())[i][2]
    # #     ang_sub4 = list(cf.pouring_water_dripper1.values())[i][1]
    # #     ang_sub5 = list(cf.pouring_water_dripper1.values())[i][0]

    # #     asyncio.run(cv.standard_spiral1(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i]))
    # #     if i==5:
    # #         print("over")

    # #두번째 
    # for i in range(1, 6):
    #     pa0 = [0.0, 1.8, 1.6, 1.8, 1.6, 1.8]
    #     spd = [0, 90, 100, 90, 100, 90]
    #     ext = [0, 45, 25, 25, 18, 1]
    #     ang = list(cf.pouring_water_dripper2.values())[i][5]
    #     ang_sub1 = list(cf.pouring_water_dripper2.values())[i][4]
    #     ang_sub2 = list(cf.pouring_water_dripper2.values())[i][3]
    #     ang_sub3 = list(cf.pouring_water_dripper2.values())[i][2]
    #     ang_sub4 = list(cf.pouring_water_dripper2.values())[i][1]
    #     ang_sub5 = list(cf.pouring_water_dripper2.values())[i][0]

    #     asyncio.run(cv.standard_spiral2(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i]))
    #     if i==5:
    #         print("over")

    # #세번째 
    # for i in range(1, 6):
    #     pa0 = [0.0, 1.8, 1.6, 1.8, 1.6, 1.8]
    #     spd = [0, 90, 100, 90, 100, 90]
    #     ext = [0, 45, 25, 25, 18, 1]
    #     ang = list(cf.pouring_water_dripper3.values())[i][5]
    #     ang_sub1 = list(cf.pouring_water_dripper3.values())[i][4]
    #     ang_sub2 = list(cf.pouring_water_dripper3.values())[i][3]
    #     ang_sub3 = list(cf.pouring_water_dripper3.values())[i][2]
    #     ang_sub4 = list(cf.pouring_water_dripper3.values())[i][1]
    #     ang_sub5 = list(cf.pouring_water_dripper3.values())[i][0]

    #     asyncio.run(cv.standard_spiral3(spd[i], ang, ang_sub1, ang_sub2, ang_sub3, ang_sub4, ang_sub5, pa0[i], ext[i]))


    
    # asyncio.run(cv.kettle_back())
    
    # asyncio.run(cv.delivery1())
    # asyncio.run(cv.delivery2())
    # asyncio.run(cv.delivery3())














    # for i in range(10):
    #     actionHome()
    #     for i in range(4):
    #         action00()
        
