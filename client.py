class TCP_Client:
    def __init__(self, username, operation, room_name):
        """
        TCPクライアントの初期化を行う。

        初期化内容:
        - ユーザー名
        - 操作種別（ルーム作成 or 参加）
        - ルーム名
        - Token（初期はNone）
        - TCPソケット生成
        """
        pass

    def connect(self):
        """
        TCPサーバに接続する。

        - 接続成功ならTrue
        - 失敗ならFalse
        """
        pass

    def start(self):
        """
        サーバにリクエストを送信し、トークンを取得する。

        処理内容:
        - リクエスト送信
        - 応答受信
        - トークン取得 self.token = 取得したtoken
        """
        pass

    def get_token(self):
        return self.token



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
        - 終了制御用イベント（stop_event）
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
        - UCRPプロトコルでパケットを解析
        - メッセージを標準出力に表示
        """
        pass

    def send_loop(self):
        """
        ユーザー入力を取得し、サーバへ送信する。

        処理内容:
        - 標準入力からメッセージを取得
        - 最大パケットサイズをチェック
        - UCRPプロトコルでパケット生成
        - UDPで送信
        - stop_eventが立ったら終了
        """
        pass


# -------------------------------
# メイン処理
# -------------------------------
"""
操作コードやユーザネームなどは
サーバに接続する"前に" 入力・バリデーションまで行い、
TCPクライアントのインスタンスに持たせて使う形を検討しています。
"""
class ChatClient:
    def run(self):
        print("=== Online Chat Messenger ===")
        print("[ Operation List ]")
        print("- 1: Create room.")
        print("- 2: Join room.")

        while True:
            try:
                operation = int(input("> Operation (1 or 2): "))
                if operation in (1, 2):
                    break
            except ValueError:
                pass
            print("[Failure] invalid input. you can enter 1 or 2.")

        room_name = input("> Room name: ")
        username = input("> User name: ")

        # ------------------
        # ユーザ・ルーム登録
        # ------------------
        tcp_client = TCP_Client(username, operation, room_name)
        connect = tcp_client.connect()
        if connect:
            pass
        else:
            # 接続に失敗したら終了
            return


        success = tcp_client.start()
        # 成功していたらトークンを取得
        if success:
            token = tcp_client.get_token()

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
    client = ChatClient()
    client.run()