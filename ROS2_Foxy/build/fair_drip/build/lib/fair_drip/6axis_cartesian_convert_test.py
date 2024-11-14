import rclpy
from rclpy.node import Node
import frrpc
import asyncio

# 로봇 IP 주소 설정
ROBOT_IP = "192.168.58.2"
robot = frrpc.RPC(ROBOT_IP)

EP = [0.0, 0.0, 0.0, 0.0]
DP = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

class GetPositionTest(Node):
    def __init__(self):
        super().__init__('get_position_test_node')
        self.get_logger().info("GetPositionTest Node Started")

    def get_current_joint_positions(self):
        try:
            result = robot.GetActualJointPosDegree(0)
            return [float(r) for r in result]
        except Exception as e:
            self.get_logger().error(f"Error getting joint positions: {e}")
            return None

def transform_pose(joint):
    try:
        pose = robot.GetForwardKin([float(j) for j in joint])
        return [pose[i] for i in range(6)]
    except Exception as e:
        print(f"Error in Cartesian transformation: {e}")
        return None

def transform_joint(pose):
    try:
        joint = robot.GetInverseKin(0, [float(p) for p in pose], -1)
        return [joint[i] for i in range(6)]
    except Exception as e:
        print(f"Error in Joint transformation: {e}")
        return None

async def PTP(J=None, SPEED=30, BLEND=-1, P=None):
    SPEED = int(SPEED)  # int로 변환
    BLEND = int(BLEND)  # int로 변환

    if P is None:
        P = transform_pose(J)
    if J is None:
        J = transform_joint(P)

    if J and P:
        # J와 P는 float 형식으로 유지
        J = [float(j) for j in J]
        P = [float(p) for p in P]
        
        # EP와 DP는 float 형식으로 유지
        EP_float = [float(e) for e in EP]
        DP_float = [float(d) for d in DP]
        
        # MoveJ 호출, 필요한 인자들은 int로 설정
        robot.MoveJ(J, P, 0, 0, SPEED, 30, BLEND, EP_float, -1, 0, DP_float)
    else:
        print("조인트 또는 포즈 값이 유효하지 않습니다.")

def main(args=None):
    rclpy.init(args=args)
    node = GetPositionTest()

    joint_positions = node.get_current_joint_positions()
    if joint_positions:
        cartesian_pose = transform_pose(joint_positions)
        if cartesian_pose:
            new_cartesian_pose = [cartesian_pose[i] + (10 if i < 3 else 0) for i in range(6)]
            new_joint_positions = transform_joint(new_cartesian_pose)
            if new_joint_positions:
                asyncio.run(PTP(new_joint_positions, SPEED=70, BLEND=-1))
                node.get_logger().info("Robot moved 1cm successfully")
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
