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
        self.room_manager = room_manager
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", self.PORT))
        self.sock.listen()

    PORT = 9001

    def start(self):
        try:
            while True:
                conn, addr = self.sock.accept()
                threading.Thread(
                    target=self.handle_room_request,
                    args=(conn, addr),
                    daemon=True
                ).start()
        finally:
            self.sock.close()

    def handle_room_request(self, conn, addr):
        try:
            operation, state, room_name, payload = TCRP.recv_packet(conn)

            if operation == TCRP.OPERATION["create_room"]:
                TCRP.send_packet(conn, None, operation, TCRP.STATE["response"], None)
            elif operation == TCRP.OPERATION["join_room"]:
                TCRP.send_packet(conn, None, operation, TCRP.STATE["response"], self.room_manager.get_room_list())
            elif operation == TCRP.OPERATION["end_sys"]:
                print("receive end system.")
                return

            operation, state, room_name, username = TCRP.recv_packet(conn)

            if operation == TCRP.OPERATION["create_room"]:
                ok, result = self.room_manager.create_room(room_name, username)
            elif operation == TCRP.OPERATION["join_room"]:
                ok, result = self.room_manager.join_room(room_name, username)
            elif operation == TCRP.OPERATION["end_sys"]:
                print("receive end system.")
                return
            else:
                ok, result = False, "Invalid operation"

            if ok:
                TCRP.send_packet(conn, room_name, operation, TCRP.STATE["complete"], result)
            else:
                TCRP.send_packet(conn, room_name, operation, TCRP.STATE["response"], result)

        except Exception as e:
            try:
                TCRP.send_packet(conn, "", 0,1, str(e))
            except Exception:
                pass
        finally:
            conn.close()


# -------------------------------
# チャットメッセージング
# 担当：kokinomu_blip
# -------------------------------
class UDP_Server:
    def __init__(self, room_manager):

        self.room_manager = room_manager
        self.sock = socket.socket(socket.AF_INET , socket.SOCK_DGRAM) #ソケット生成
        self.sock.bind(('127.0.0.1' , self.PORT))

    PORT = 9002
    MAX_PACKET_SIZE = 4096

    TIMEOUT = 30 # タイムアウト/タイムアウトに判定する非操作時間
    CHECK_INTERVAL = 1 # タイムアウト/チェック間隔

    def start(self):
        while True :
            data, addr = self.sock.recvfrom(self.MAX_PACKET_SIZE)
            room_name, token, msg = UCRP.parse_packet(data)

            ok, validate_msg = self.validate_packet(addr , room_name , token)
            if not ok:
                packet= UCRP.build_packet(room_name, token, validate_msg)
                print(validate_msg)
                self.sock.sendto(packet, addr)
                continue

            #メッセージに名前を追加
            client = self.room_manager.get_client(room_name, token)
            username = client["username"]

            #退出用メッセージを受け取った時
            if msg == UCRP.SYSTEM_MSG["leave_room"]:
                host_token = self.room_manager.get_host_token(room_name)

                if token == host_token:
                    notice_msg = UCRP.SYSTEM_MSG["host_leave"]
                else:
                    notice_msg = f"- [left] {username}"
                self.broadcast(room_name, UCRP.build_packet(room_name, token, notice_msg))
                ok , result_msg = self.room_manager.leave_room(room_name , token)
                print(result_msg)

                continue

            client["last_seen"] = time.time() #最後の入力時点の時間を更新

            if msg == UCRP.SYSTEM_MSG["join_room"]:
                msg = f"+ [join] {username}"
                packet = UCRP.build_packet(room_name, token, msg)
                self.broadcast(room_name, packet)
                continue

            msg = f'{username}: {msg}'

            packet = UCRP.build_packet(room_name , token , msg)
            self.broadcast(room_name , packet)



    def validate_packet(self, addr, room_name, token):
        if room_name not in self.room_manager.rooms :
            return False, f'[Failure] room name "{room_name}" does not exist.'

        if not self.room_manager.get_client(room_name , token) :
            return False, f'[Failure] token "{token}" is unknown token.'

        client = self.room_manager.get_client(room_name, token)
        client["addr"] = addr

        return True, "OK"

    # タイムアウト処理
    def timeout_detection(self):
        while True:
            now = time.time()
            remove_list = []

            for room in list(self.room_manager.rooms.values()) :
                for (token, client) in room.get_clients().items() :
                    last_seen = client["last_seen"]
            
                    #30秒以上でタイムアウト処理            
                    if now - last_seen > self.TIMEOUT :
                        remove_list.append((room.name , token))
                        continue

            for (room_name, token) in remove_list :
                self.room_manager.leave_room(room_name , token)
            
            time.sleep(self.CHECK_INTERVAL)


    def broadcast(self, room_name, packet):
        clients = self.room_manager.get_clients(room_name)
        if  clients is not None:
            for client in clients.values() :
                if client["addr"] is not None:
                    self.sock.sendto(packet , client["addr"])


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
            ok, result = room.add_client(host_token, username)
            if ok:
                print(f'[Success] room name "{room_name}" created.')
                self.rooms[room_name] = room
                return True, host_token
            else:
                return False, result

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

    def get_host_token(self, room_name):
        with self.lock:
            room = self.rooms.get(room_name)
            return None if room is None else room.host_token

    def get_client(self, room_name, token):
        with self.lock:
            room = self.rooms.get(room_name)
            return None if room is None else room.get_client(token)

    def get_clients(self, room_name):
        with self.lock:
            room = self.rooms.get(room_name)
            return None if room is None else room.get_clients()

    # ルーム名を配列で取得
    def get_room_list(self):
        with self.lock:
            room_list = self.rooms.keys()
            if not room_list:
                return ["The room has not been created yet."]
            else:
                return list(room_list)


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
                    return False, f'username "{username}" already exists.'

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
        print("=== Online Chat Messenger Server ===")
        print("exit with Ctrl+C. waiting message...")
        # 各サーバのインスタンスを作成。共通のルームマネージャーを持ってもらう。
        tcp_server = TCP_Server(self.room_manager)
        udp_server = UDP_Server(self.room_manager)
        # デーモンスレッドで各サーバを起動
        threading.Thread(target=tcp_server.start, daemon=True).start()
        threading.Thread(target=udp_server.start, daemon=True).start()
        threading.Thread(target=udp_server.timeout_detection, daemon=True).start()

        # メインスレッド用ループ
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nCtrl+C received.\nServer will be shut down.")
        finally:
            rooms = udp_server.room_manager.get_room_list()
            for room in rooms:
                udp_server.broadcast(room, UCRP.build_packet(room, None, UCRP.SYSTEM_MSG["server_stop"]))


# python3 server.pyでサーバが起動
if __name__ == "__main__":
    try:
        server = ChatServer()
        server.run()
    finally:
        ("----- end -----")
