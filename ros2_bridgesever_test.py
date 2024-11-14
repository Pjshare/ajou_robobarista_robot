import asyncio
import websockets
import json

# 웹소켓 서버 URI (rosbridge의 기본 포트는 9090)
WS_SERVER_URI = "ws://192.168.58.27:9090"

async def send_message_to_rosbridge():
    try:
        # 웹소켓 서버에 연결
        async with websockets.connect(WS_SERVER_URI) as websocket:
            # ROS 브리지에 보낼 메시지 정의 (예: /chatter 토픽에 퍼블리시)
            message = {
                "op": "publish",
                "topic": "/vision",
                "type": "std_msgs/String",
                "msg": {
                    "data": json.dumps({
                        "dripper": [
                            {
                                "order": 1,
                                "coordinate": [300,38,339,124],
                                "center": [], 
                                "exist_dripper": True,
                                "exist_coffee_beans":  True
                            },
                            {
                                "order": 2,
                                "coordinate": [324,74,366,156],
                                "center": [],
                                "exist_dripper": True,
                                "exist_coffee_beans":  False
                            },
                            {
                                "order": 3,
                                "coordinate": [350,104,400,200],
                                "center": [],
                                "exist_dripper": False,
                                "exist_coffee_beans":  True
                            }
                        ],
                        "cup": [
                            {
                                "order": 1,
                                "coordinate": [271,480,322,591],
                                "center": [],
                                "exist_cup": True
                            },
                            {
                                "order": 2,
                                "coordinate": [329,418,376,521],
                                "center": [],
                                "exist_cup": True
                            },
                            {
                                "order": 3,
                                "coordinate": [383,371,426,466],
                                "center": [],
                                "exist_cup": False
                            }
                        ],
                        "pot": []
                    })
                }
            }

            # JSON 형식으로 메시지 전송
            await websocket.send(message)
            print(f"Sent message: {message}")

            # # 응답 받기 (선택 사항, rosbridge는 기본적으로 응답을 주지 않음)
            # response = await websocket.recv()
            # print(f"Received response: {response}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(send_message_to_rosbridge())
