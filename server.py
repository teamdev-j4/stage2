import socket
import threading
import time
import secrets

from protocol import TCRP, UCRP


# ルームやクライアントの情報へは、必ずRoomManagerのインスタンスメソッドを使ってアクセスしてください。
# """説明文"""は、ご自身の担当分を自由に消去・編集OKです。最終的には消去します。

# -------------------------------
# ユーザー登録 / ルーム作成・参加
# 担当：wmelon89
# -------------------------------
class TCP_Server:
    def __init__(self, room_manager):
        """
        TCPサーバの初期化を行う。

        初期化内容:
        - RoomManagerへの参照を保持
        - TCPソケットを生成
        - 指定アドレスとポートにバインド
        - 接続待ち状態（listen）にする
        """

    PORT = 9001

    def start(self):
        """
        TCPサーバを起動し、クライアントからの接続を待ち受ける。

        - 無限ループで接続をacceptする
        - 接続ごとにスレッドを作成し、handle_room_requestを実行する
        - サーバ終了時はソケットを閉じる
        """
        pass

    def handle_room_request(self, conn, addr):
        """
        クライアントからのルーム操作要求を処理する。

        処理内容:
        - TCRPプロトコル(TCRPのrecv_packet(conn))でパケットを受信
        - operationに応じて以下を分岐
            - ルーム作成(1) → self.room_manager.create_room
            - ルーム参加(2) → self.room_manager.join_room
            返り値で成功・失敗をチェックして処理を分岐
        - 成功時はトークンを返す(state: 2)
        - 失敗時はエラーメッセージを返す(state: 1)
          (ルーム名・ユーザ名の重複、不正なコードなど)
        - 最後に接続を閉じる
        """
        pass

# -------------------------------
# チャットメッセージング
# 担当：kokinomu_blip
# -------------------------------
class UDP_Server:
    def __init__(self, room_manager):

        self.room_manager = room_manager
        self.sock = socket.socket(socket.AF_INET , socket.SOCK_DGRAM) #ソケット生成
        self.sock.bind(('127.0.0.1' , self.PORT))
        """
        UDPサーバの初期化を行う。

        初期化内容:
        - RoomManagerへの参照を保持
        - UDPソケット生成
        - UDPソケットをバインド
        """

    PORT = 9002

    MAX_PACKET_SIZE = 4096

    def start(self):
        while True :
            data, addr = self.sock.recvfrom(self.MAX_PACKET_SIZE)
            room_name, token, msg = UCRP.parse_packet(data)
            if not self.validate_packet(addr , room_name , token) :
                continue
            
            #退出用メッセージを受け取った時
            if msg == 'mL8^XTqV@gGE' :
                is_succese , msg = self.room_manager.leave_room(room_name , token)

            packet = UCRP.build_packet(room_name , token , msg)
            self.broadcast(room_name , packet)


        """
        UDPサーバを起動し、チャットメッセージを処理する。

        処理内容:
        - クライアントからメッセージを受信
        - パケットを解析（UDRPのparse_packet()）
        - トークンとアドレスの検証(validate_packet)
        - メッセージ内容に応じて処理
            - 退室メッセージ → 退出処理
            - それ以外 → 通常メッセージ
        - 同一ルーム内の全クライアントへブロードキャスト
        """

        pass

    def validate_packet(self, addr, room_name, token):
        if room_name not in self.room_manager.rooms :
            return False
    
        if not self.room_manager.get_client(room_name , token) :
            return False
        
        client = self.room_manager.get_client(room_name, token)
        client["addr"] = addr
        
        return True
        
        
        """
        受信したUDPパケットの正当性を検証する。

        検証内容:
        - ルームが存在するか
        - トークンがルーム内に存在するか
        - 通信時はアドレスを登録しなおす
        """

    def broadcast(self, room_name, packet):
        clients = self.room_manager.get_clients(room_name)
        if  clients is not None:
            for client in clients.values() :
                if client["addr"] is not None:
                    self.sock.sendto(packet , client["addr"])
        """
        指定されたルーム内の全クライアントにパケットを送信する。

        処理内容:
        - ルームの全クライアントを取得
        - 各クライアントのアドレスにsendtoで送信
        """
        pass


# -------------------------------
# ルーム管理
# 担当：Nonnok
# -------------------------------
class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.lock = threading.RLock()

    def create_room(self, room_name, username):
        with self.lock:
            # ルーム名の重複を排除
            if room_name in self.rooms:
                return False, f'[Failure] room name "{room_name}" is already exists.'

            host_token = secrets.token_hex(16)
            room = Room(room_name, host_token)
            success, _ = room.add_client(host_token, username)
            if success:
                print(f'[Success] room name "{room_name}" created.')
                self.rooms[room_name] = room
                return True, host_token
            else:
                return False, "failed to add host"

    def join_room(self, room_name, username):
        with self.lock:
            room = self.rooms.get(room_name)
        if room is None:
            return False, f'room "{room_name}" does not exist.'

        token = secrets.token_hex(16)
        ok, result = room.add_client(token, username)
        if ok:
            return True, token
        else:
            return False, result

    def leave_room(self, room_name, token):
        with self.lock:
            room = self.rooms.get(room_name)

        if room is None:
            return False, "room not found."

        status, username = room.delete_client(token)

        if status == "HOST_LEFT":
            with self.lock:
                self.rooms.pop(room_name, None)
            return True, f"- host {username} left, room closed."

        if status == "OK":
            return True, f"- {username} left."

        return False, "client not found."


# -------------------------------
# ルームクラス
# -------------------------------
class Room:
    def __init__(self, name, host_token):
        self.name = name
        self.host_token = host_token
        self.clients = {}
        self.lock = threading.RLock()

    def get_client(self, token):
        with self.lock:
            client = self.clients.get(token)
            if client:
                return client
            else:
                return None

    def get_clients(self):
        return {
            key: dict(value)
            for key, value in self.clients.items()
        }

    def has_clients(self, token):
        with self.lock:
            return token in self.clients

    def add_client(self, token, username, addr=None):
        with self.lock:
            # usernameの重複チェック
            for client in self.clients.values():
                if client["username"] == username:
                    return False, username

            self.clients[token] = {
                "username": username,
                "addr": addr,
                "last_seen": time.time()
            }
            print(f'+ added {self.clients[token]["username"]}')
            return True, username

    def delete_client(self, token):
        with self.lock:
            if token in self.clients:
                username = self.clients[token]["username"]
                del self.clients[token]

                if token == self.host_token:
                    return "HOST_LEFT", username

                return "OK", username
            else:
                return "NOT_FOUND", username



# -------------------------------
# サーバ全体の制御
# -------------------------------
class ChatServer:
    def __init__(self):
        # ルームマネージャーを初期化
        self.room_manager = RoomManager()

    def run(self):
        # 各サーバのインスタンスを作成。共通のルームマネージャーを持ってもらう。
        tcp_server = TCP_Server(self.room_manager)
        udp_server = UDP_Server(self.room_manager)
        # デーモンスレッドで各サーバを起動
        threading.Thread(target=tcp_server.start, daemon=True).start()
        threading.Thread(target=udp_server.start, daemon=True).start()

        # メインスレッド用ループ
        while True:
            time.sleep(1)


# python3 server.pyでサーバが起動
if __name__ == "__main__":
    server = ChatServer()
    server.run()
