
import frrpc
import conf_file as cf
import time
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
    
    actionHome()
    action00()
    
    actionHome()
    # for i in range(10):
    #     actionHome()
    #     for i in range(4):
    #         action00()
        