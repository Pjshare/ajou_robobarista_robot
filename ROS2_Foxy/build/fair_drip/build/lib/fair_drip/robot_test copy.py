
import frrpc
import conf_file as cf
import time
import control_v2
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
    pos0 = [1.327,-130.671,139.899,-101.789,87.985,89.265]
    PTP(pos0, 30, -1)

def action00():
    robot_main = frrpc.RPC(ROBOT_IP)
    # control = RobotControl(robot_main)
    speed = 30
    robot.SetSpeed(speed)
    SPEED = float(100)
    DP1 = [0.000, 0.000, 0.000, 0.0, 0.000, 0.000]
    Pa1 = [2.0, 0.0, 0.0, 20.0, 20.0, 0.0]
    pos1 = [14.485, -93.489, 110.195, -103.067, 57.88, 89.264]
    pos2 = [-14.485, -93.489, 110.195, -103.067, 113.866, 89.264]
    PTP(pos1, 100, -1)
    PTP(pos2, 100, -1)

def newSPIRAL(J1, SPEED, Pa, DP):
    P1 = transform_pose(J1)
    robot.NewSpiral(J1, P1, 0, 0, float(SPEED), 0.0, EP2, 50.0, 2, DP, Pa)

    while True:
        motion_state = robot.GetRobotMotionDone()
        if motion_state[1] == 1:
            break
        time.sleep(0.1)
        
def movegripper(index, pos, vel, force, max_time, last_arg=0):
    robot.MoveGripper(index, pos, vel, force, max_time, last_arg)
    start_time = time.time()
    while time.time() - start_time < 1.0:  
        gripper_state = robot.GetGripperMotionDone()
        if gripper_state[2] == 1:  
            break
        print("Gripper moving ready...")
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
    #초기 위치로 이동
    #actionHome()
    #action00()

    # 현재 조인트 위치를 얻고 이를 사용해 Cartesian 좌표로 변환
    current_joint_positions = control_v2.get_current_joint_positions()
    cartesian_pose = control_v2.transform_pose(current_joint_positions)

    # 변환된 Cartesian pose 출력
    print(f"현재 Cartesian 좌표: {cartesian_pose}")

    # x, y, z 좌표를 각각 3cm씩 이동시키기
    new_cartesian_pose = cartesian_pose.copy()  # 원래 pose를 복사하여 수정
    new_cartesian_pose[0] += 0.03  # x 좌표에 3cm 더함
    new_cartesian_pose[1] += 0.03  # y 좌표에 3cm 더함
    new_cartesian_pose[2] += 0.03  # z 좌표에 3cm 더함

    # 이동 후의 Cartesian 좌표 출력
    print(f"3cm 이동 후 Cartesian 좌표: {new_cartesian_pose}")

    # Cartesian 좌표를 조인트 좌표로 변환
    new_joint_positions = control_v2.transform_joint(new_cartesian_pose)

    # 새로운 조인트 좌표로 이동 (비동기 함수 실행)
    asyncio.run(control_v2.PTP(new_joint_positions, SPEED=70.0, BLEND=-1))

    print("로봇이 3cm 이동 완료") 
    #actionHome()
    #action00()
    # asyncio.run(control_v2.beancup_pick())
    # asyncio.run(control_v2.beancup_dropbean_ready()) 
    # asyncio.run(control_v2.beancup_dropbean_1())
    # asyncio.run(control_v2.beancup_dropbean_ready()) 
    # asyncio.run(control_v2.beancup_dropbean_2())
    # asyncio.run(control_v2.beancup_dropbean_ready()) 
    # asyncio.run(control_v2.beancup_dropbean_3())
    # asyncio.run(control_v2.beancup_dropbean_ready()) 
    # asyncio.run(control_v2.beancup_back())
    # asyncio.run(control_v2.new_preparing_pick_dripper()) 
    # asyncio.run(control_v2.shaking_dripper1()) 
    # asyncio.run(control_v2.new_preparing_pick_dripper()) 
    movegripper(1,100,50,50,10000,0)
    #asyncio.run(control_v2.kettle_pick()) 
    
    #actionHome()
    # for i in range(10):
    #     actionHome()
    #     for i in range(4):
    #         action00()
        
