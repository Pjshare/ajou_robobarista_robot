import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import asyncio
import websockets  # 웹소켓 라이브러리
import json

class RobotListener(Node):
    def __init__(self):
        super().__init__('robot_listener')
        # ROS2 서브스크라이버 설정
        self.subscription = self.create_subscription(
            String,
            '/robot',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        # 웹소켓 설정
        self.websocket_uri = "ws://127.0.0.1:9090"
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.connect_websocket())  # 웹소켓 연결
        self.loop.create_task(self.receive_websocket_message())  # 웹소켓 메시지 수신

    def listener_callback(self, msg):
        # ROS2 토픽에서 메시지 수신
        self.get_logger().info(f'Received from /robot: {msg.data}')

    async def connect_websocket(self):
        try:
            self.websocket = await websockets.connect(self.websocket_uri)
            self.get_logger().info(f'Connected to WebSocket server at {self.websocket_uri}')
        except Exception as e:
            self.get_logger().error(f"Failed to connect to WebSocket server: {e}")

    async def receive_websocket_message(self):
        # 웹소켓으로부터 메시지 수신
        while True:
            try:
                message = await self.websocket.recv()
                self.get_logger().info(f'Received from WebSocket: {message}')
                # 웹소켓 메시지를 ROS2 토픽으로 발행하는 동작을 추가하려면 여기에 작성
            except Exception as e:
                self.get_logger().error(f"Error receiving message from WebSocket: {e}")
                break

def main(args=None):
    rclpy.init(args=args)

    # listener 노드 실행
    robot_listener = RobotListener()

    # ROS2 노드 동작 유지
    rclpy.spin(robot_listener)

    # 노드 종료
    robot_listener.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
