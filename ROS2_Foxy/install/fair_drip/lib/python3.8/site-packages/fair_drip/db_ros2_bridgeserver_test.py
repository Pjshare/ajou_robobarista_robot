import websocket
import json
import threading
import time  # For controlling the interval between messages

# 웹소켓 서버의 주소
URL = "ws://192.168.58.8:9090"

def send_message(ws):
    while True:
        msg = {
            "op": "publish",
            "topic": "/drip",
            "msg": {
                "data": "xyz"
            }
        }
        ws.send(json.dumps(msg))
        print("메시지 발행 :", msg)
        time.sleep(5)  # Wait for 5 seconds before sending the next message (adjust as needed)

def on_open(ws):
    # Start a new thread to send messages continuously
    threading.Thread(target=send_message, args=(ws,)).start()

def on_error(ws, error):
    print("웹소켓 오류 :", error)

def on_close(ws):
    print("웹소켓 연결이 종료")

if __name__ == "__main__":
    ws = websocket.WebSocketApp(URL,
                                on_open=on_open,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

