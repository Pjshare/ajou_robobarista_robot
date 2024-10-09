import websocket
import json

# 웹소켓 서버의 주소
URL = "ws://192.168.58.16:9090"  

def on_open(ws):
    msg = {
        "op": "publish",
        "topic": "/drip",  
        "type" : "std_msgs/String",
        "msg": {
            "data": "xyz"
        }

        #while 
    }

    ws.send(json.dumps(msg))
    print("메시지 :", msg)

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
