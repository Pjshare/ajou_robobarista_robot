import rclpy
from rclpy.node import Node
import frrpc  # RPC를 이용해 로봇 제어
import time

# 로봇 IP 주소 설정
ROBOT_IP = "192.168.58.2" 
robot = frrpc.RPC(ROBOT_IP)

class GetPositionTest(Node):
    def __init__(self):
        super().__init__('get_position_test_node')
        self.get_logger().info("GetPositionTest Node Started")
    
    def get_current_joint_positions(self):
        # 조인트의 값을 저장할 변수를 선언
        joint_positions = [0.0] * 6  # 6개의 조인트 각도를 저장할 배열
        
        # GetActualJointPosDegree 함수 호출
        try:
            # joint_positions 배열에 값을 저장하도록 설정
            self.get_logger().info(f"joint_positions 초기값: {joint_positions}")
            
            # 조인트 위치를 가져오는 함수 호출, return 형식을 수정
            result = robot.GetActualJointPosDegree(0)  # 함수가 값을 반환하도록 설정
            self.get_logger().info(f"조인트 위치: {result}")
            
            # 결과가 있으면 반환, 없으면 None 반환
            if result:
                return result
            else:
                self.get_logger().error(f"조인트 위치를 가져오는 중 에러 발생: {result}")
                return None
        except Exception as e:
            self.get_logger().error(f"조인트 위치를 가져오는 중 예외 발생: {e}")
            return None

def main(args=None):
    rclpy.init(args=args)
    
    # GetPositionTest 인스턴스를 생성하고 조인트 위치 가져오기
    test_node = GetPositionTest()
    
    # 현재 조인트 위치를 얻기 위한 함수 호출
    joint_positions = test_node.get_current_joint_positions()
    
    if joint_positions:
        test_node.get_logger().info(f"현재 조인트 위치: {joint_positions}")
    else:
        test_node.get_logger().error("조인트 위치를 가져오는 데 실패했습니다.")
    
    # ROS2 노드 종료
    test_node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
