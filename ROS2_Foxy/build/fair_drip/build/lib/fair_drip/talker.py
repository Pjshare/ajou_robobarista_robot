import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import asyncio
import websockets  # 웹소켓 라이브러리

class RobotTalker(Node):
    def __init__(self):
        super().__init__('robot_talker')
        # ROS2 퍼블리셔 설정
        self.publisher_ = self.create_publisher(String, '/robot', 10)
        timer_period = 2.0  # 2초마다 메시지 발행
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0  # 메시지 카운터
        
        # 웹소켓 설정
        self.websocket_uri = "ws://127.0.0.1:9090"
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.connect_websocket())  # 웹소켓 연결

    async def connect_websocket(self):
        try:
            self.websocket = await websockets.connect(self.websocket_uri)
            self.get_logger().info(f'Connected to WebSocket server at {self.websocket_uri}')
        except Exception as e:
            self.get_logger().error(f"Failed to connect to WebSocket server: {e}")

    async def send_websocket_message(self, message):
        if self.websocket and self.websocket.open:
            await self.websocket.send(message)
            self.get_logger().info(f'Sent to WebSocket: {message}')
        else:
            self.get_logger().error('WebSocket is not connected.')

    def timer_callback(self):
        # ROS2 토픽에 메시지 발행
        msg = String()
        msg.data = f'Robot status update {self.i}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published to /robot: {msg.data}')  # 로그 출력

        # 웹소켓으로 메시지 전송
        websocket_msg = f'WebSocket message: Robot status {self.i}'
        asyncio.run_coroutine_threadsafe(self.send_websocket_message(websocket_msg), self.loop)

        self.i += 1  # 메시지 카운터 증가

def main(args=None):
    rclpy.init(args=args)

    # talker 노드 실행
    robot_talker = RobotTalker()

    # ROS2 노드 동작 유지
    rclpy.spin(robot_talker)

    # 노드 종료
    robot_talker.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

