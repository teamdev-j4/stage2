import socket
import threading
from protocol import TCRP, UCRP
# -------------------------------
# ユーザー登録 / ルーム作成・参加
# 担当：wmelon89
# -------------------------------
class TCP_Client:
    HOST = "127.0.0.1"
    PORT = 9001

    def __init__(self):
        self.username = None
        self.room_name = None
        self.token = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.sock.connect((self.HOST,self.PORT))
            print(f"[Connected] {self.HOST}:{self.PORT} (TCP)")
            return True
        except Exception:
            print(f"[Failure] Can't connected.")
            return False

    @staticmethod
    def input_operation(nums):
        while True:
            try:
                operation = int(input(f"> Operation ({' or '.join(map(str, nums))}): "))
                if operation in nums:
                    return operation
            except ValueError:
                pass
            print(f"[Failure] invalid input. you can enter {' or '.join(map(str, nums))}.")

    def start(self):
        try:
            print("=== Online Chat Messenger ===")
            print("\n[ Operation List ]")
            print("- 1: Create room.")
            print("- 2: Join room.")
            print("- 0: End system.\n")

            operation = self.input_operation([1, 2, 0])
            if operation == 0:
                TCRP.send_packet(self.sock, self.room_name, operation, TCRP.STATE["request"], self.username)
                return 0

            #サーバにリクエスト送信
            TCRP.send_packet(
                self.sock,
                self.room_name,
                operation,
                TCRP.STATE["request"], #request
                self.username
                )

            #応答受信
            operation, state, _, payload = TCRP.recv_packet(self.sock)

            if not payload:
                pass
            elif payload:
                if len(payload) == 1 and payload[0] == "The room has not been created yet.":
                    print(f"\n[Not exist] {payload[0]}\n")
                    print("[ Operation List ]")
                    print("- 1: Create room.")
                    print("- 0: End system.\n")
                    operation = self.input_operation([1, 0])
                    if operation == 0:
                        TCRP.send_packet(self.sock, self.room_name, operation, TCRP.STATE["request"], self.username)
                        return 0
                else:
                    print("[ Room List ]")
                    for item in payload:
                        print(f"- {item}")

            self.room_name = input("> Room name: ")
            self.username = input("> User name: ")

            TCRP.send_packet(
                self.sock,
                self.room_name,
                operation,
                TCRP.STATE["request"],
                self.username
            )

            operation, state, room_name, payload = TCRP.recv_packet(self.sock)

            if state == TCRP.STATE["complete"]: #success
                self.token = payload
                return True
            else:
                print(payload)
                return False
        except KeyboardInterrupt:
            print("\nCtrl+C received.\nChat ended.")
            return 0
        except ConnectionResetError:
            print(f"- server stopped.\n--- system shutt down...")
        finally:
            self.sock.close()
            print(f"[Disconnected] {self.HOST}:{self.PORT} (TCP)")

    def get_token(self):
        return self.token


# -------------------------------
# チャットメッセージング
# 担当：kokinomu_blip
# -------------------------------
class UDP_Client:
    HOST = "127.0.0.1"
    PORT = 9002

    def __init__(self, username, room_name, token):
        self.username = username
        self.room_name = room_name
        self.token = token

        self.sock = socket.socket(socket.AF_INET , socket.SOCK_DGRAM) #ソケット生成
        self.server_address = (self.HOST , self.PORT) #サーバアドレス

        self.stop_Event = threading.Event()



    def start(self):
        print(f"[Connected] {self.HOST}:{self.PORT} (UDP)")
        send_thread = threading.Thread(target=self.send_loop, daemon=True)
        send_thread.start()

        try:
            self.recv_loop()
        #Ctrl-cが入力された場合
        except KeyboardInterrupt :
            print('\nCtrl+C received.')
        finally:
            #退出用メッセージを送信
            UCRP_packet = UCRP.build_packet(self.room_name , self.token , UCRP.SYSTEM_MSG["leave_room"])
            self.sock.sendto(UCRP_packet ,(self.server_address))
            self.stop_Event.set()
            print(f"[Disconnected] {self.HOST}:{self.PORT} (TCP)")
            #終了処理
            print('See you next time!')
            self.sock.close()


    def recv_loop(self):
        self.sock.settimeout(1)
        while not self.stop_Event.is_set() :
            try :
                #データを受け取り、メッセージを表示
                data, address = self.sock.recvfrom(4096)
                room, token, msg = UCRP.parse_packet(data)

                if msg == UCRP.SYSTEM_MSG["host_leave"]:
                    print(f"- host user left.\n--- close the room...")
                    self.stop_Event.set()

                elif msg == UCRP.SYSTEM_MSG["server_stop"]:
                    print(f"- server stopped.\n--- system shutt down...")
                    self.stop_Event.set()

                elif msg == UCRP.SYSTEM_MSG["timeout"]:
                    print(f"- host user timeout.\n--- system shutt down...")
                    self.stop_Event.set()

                else:
                    print(msg)
                    print("> ", end="", flush=True)

            except socket.timeout :
                continue

            except Exception as e :
                print(e)
                self.stop_Event.set()


    def send_loop(self):
        packet = UCRP.build_packet(self.room_name, self.token, UCRP.SYSTEM_MSG["join_room"])
        self.sock.sendto(packet, self.server_address)
        while not self.stop_Event.is_set() :

            print(f"> ", end="", flush=True)
            user_msg = input()

            #4096バイトより長ければ入力させる
            if len(user_msg.encode('utf-8')) > 4096 :
                print("The message is too long")
                continue

            #パケット生成して送信
            UCRP_packet = UCRP.build_packet(self.room_name , self.token , user_msg)
            self.sock.sendto(UCRP_packet ,(self.server_address))


# -------------------------------
# メイン処理
# -------------------------------
class ChatClient:
    def run(self):
        # ------------------
        # ユーザ・ルーム登録
        # ------------------
        tcp_client = TCP_Client()
        connect = tcp_client.connect()
        if connect:
            pass
        else:
            # 接続に失敗したら終了
            return


        ok = tcp_client.start()
        # 成功していたらトークンを取得
        if ok:
            username = tcp_client.username
            room_name = tcp_client.room_name
            token = tcp_client.get_token()
        elif ok == 0:
            return
        else:
            # 取得に失敗したら終了
            print("[Failure] Failed to obtain token.")
            return False

        # ------------------
        # チャット開始
        # ------------------
        udp_client = UDP_Client(username, room_name, token)
        udp_client.start()


# python3 client.pyでクライアント登録〜チャットまでの手順が開始
if __name__ == "__main__":
    try:
        client = ChatClient()
        client.run()
    except KeyboardInterrupt:
        print("\nCtrl+C received.")
