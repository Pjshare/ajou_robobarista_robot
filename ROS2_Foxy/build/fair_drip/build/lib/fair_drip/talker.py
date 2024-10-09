# -*- coding: UTF-8 -*-

import asyncio
import websockets  # type: ignore
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# 웹소켓 서버의 주소
WS_SERVER_URI = "ws://127.0.0.1:9090"

class Talker(Node):
    def __init__(self):
        super().__init__('talker')
        # /drip 토픽으로 메시지 퍼블리싱
        self.publisher_ = self.create_publisher(String, '/drip', 10)
        self.loop = asyncio.get_event_loop()
        # 웹소켓에서 메시지를 받는 태스크 실행
        self.loop.create_task(self.websocket_listener())

    async def websocket_listener(self):
        """웹소켓 서버에서 메시지를 받아 ROS2 토픽으로 퍼블리시하는 함수"""
        try:
            # 웹소켓 서버에 연결
            async with websockets.connect(WS_SERVER_URI) as websocket:
                self.get_logger().info(f"Connected to WebSocket server: {WS_SERVER_URI}")

                # 무한 루프를 통해 지속적으로 웹소켓 메시지 수신
                while True:
                    # 웹소켓 서버로부터 메시지 수신
                    message = await websocket.recv()
                    self.get_logger().info(f"Received message from WebSocket: {message}")

                    # 메시지를 ROS2 String 메시지로 변환하여 퍼블리시
                    ros_message = String()
                    ros_message.data = message  # 웹소켓 메시지를 그대로 사용
                    self.publisher_.publish(ros_message)  # /drip 토픽으로 퍼블리시

                    self.get_logger().info(f"Published message to /drip: {ros_message.data}")
        except websockets.ConnectionClosed as e:
            self.get_logger().error(f"WebSocket connection closed: {e}")
        except Exception as e:
            self.get_logger().error(f"An error occurred: {e}")

def main(args=None):
    rclpy.init(args=args)
    talker = Talker()

    # ROS2 노드를 비동기적으로 스핀
    try:
        rclpy.spin(Talker)
    except KeyboardInterrupt:
        pass
    finally:
        talker.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

