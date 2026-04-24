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
                operation = int(input(f"> Operation ({" or ".join(map(str, nums))}): "))
                if operation in nums:
                    return operation
            except ValueError:
                pass
            print(f"[Failure] invalid input. you can enter {" or ".join(map(str, nums))}.")

    def start(self):
        try:
            print("=== Online Chat Messenger ===")
            print("\n[ Operation List ]")
            print("- 1: Create room.")
            print("- 2: Join room.")
            print("- 0: End system.\n")

            operation = self.input_operation([1, 2, 0])
            if operation == 0:
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
    def __init__(self, username, room_name, token):
        """
        UDPクライアントの初期化を行う。

        設定内容:
        - ユーザー名
        - ルーム名
        - 認証トークン
        - サーバアドレス（IP, PORT）
        - ソケット生成
        - 終了制御用イベント（threading.Event()）
        """
        pass

    def start(self):
        """
        チャットの送受信処理を開始する。

        処理内容:
        - 送信用スレッド(send_loop)を起動
        - メインスレッドで受信処理(recv_loop)を実行
        - Ctrl+C入力時は退出メッセージを送信し終了する
        """
        pass

    def recv_loop(self):
        """
        サーバからのメッセージを受信し表示する。

        処理内容:
        - UDPでデータを受信
        - UCRPプロトコル(parse_packet)でパケットを解析
        - メッセージを標準出力(print)に表示
        """
        pass

    def send_loop(self):
        """
        ユーザー入力(input)を取得し、サーバへ送信する。

        処理内容:
        - 標準入力からメッセージを取得
        - 最大パケットサイズ(4096Bite)をチェック
        - UCRPプロトコルでパケット生成(build_packet)
        - UDPで送信(sendto())
        - stop_eventが立ったら終了
        """
        pass


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