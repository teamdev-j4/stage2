import json

# -------------------------------
# TCRP (Chat room protocol / TCP)
# -------------------------------
class TCRP:
    HEADER_SIZE = 32

    OPERATION = {
    "create_room": 1,
    "join_room": 2,
    "end_sys": 0,
    }

    STATE = {
        "request": 0,
        "response": 1,
        "complete": 2,
    }

    @classmethod
    # 受け取って解析し、結果を返す。
    def recv_packet(self, sock):
        header = SocketHelper.recv_exact(sock, self.HEADER_SIZE)
        room_name_len, operation, state, payload_len = self.parse_header(header)

        # bodyがない場合はNoneを返す
        if room_name_len + payload_len == 0:
            return operation, state, None, None

        body = SocketHelper.recv_exact(sock, room_name_len + payload_len)
        room_name, payload = self.parse_body(body, room_name_len, payload_len)

        return operation, state, room_name, payload

    # ヘッダー部分の解析
    @staticmethod
    def parse_header(header):
        room_name_len = header[0]
        operation = header[1]
        state = header[2]
        payload_len = int.from_bytes(header[3:32], "big")

        return room_name_len, operation, state, payload_len

    # ボディー部分の解析
    @staticmethod
    def parse_body(body, room_name_len, payload_len):
        room_name = body[:room_name_len].decode("utf-8")

        if payload_len > 0:
            payload = body[room_name_len:].decode("utf-8")
            data = json.loads(payload)
        else:
            data = None

        return room_name, data

    # TCPパケットを生成して送信する。
    @classmethod
    def send_packet(self, sock, room_name, operation, state, payload):
        body = b""

        if room_name is None:
            room_name_len = 0
        else:
            room_name_b = room_name.encode("utf-8")
            room_name_len = len(room_name_b)
            body += room_name_b

        if payload is None:
            payload_len = 0
        else:
            payload_b = json.dumps(payload).encode("utf-8")
            payload_len = len(payload_b)
            body += payload_b

        header = self.build_header(room_name_len, operation, state, payload_len)

        sock.sendall(header)
        sock.sendall(body)

    # TCPパケットのヘッダーを作成する。
    @staticmethod
    def build_header(room_name_len, operation, state, payload_len):
        return (
            room_name_len.to_bytes(1, "big")
            + operation.to_bytes(1, "big")
            + state.to_bytes(1, "big")
            + payload_len.to_bytes(29, "big")
        )


# -------------------------------
# UCRP (Chat room protocol / UDP)
# -------------------------------
class UCRP:
    SYSTEM_MSG = {
        "join_room": "2=6nF_du@&XS",
        "leave_room": "mL8^XTqV@gGE",
        "host_leave": "Bxp>Yd+OS7Mp",
        "server_stop": "E|8b_hglFrq=",
        "timeout": "7ZP$uh7=O^0s",
    }

    # パケットを解析する
    @staticmethod
    def parse_packet(data):
        room_name_size = data[0]
        token_size = data[1]
        token_start = 2 + room_name_size
        token_end = token_start + token_size

        room = data[2:token_start].decode("utf-8")
        token = data[token_start:token_end].decode("utf-8")
        msg = data[token_end:].decode("utf-8")

        return room, token, msg

    # パケットを作成する。
    @staticmethod
    def build_packet(room_name, token, msg):
        room_name_b = room_name.encode("utf-8")
        if token is None:
            token_b = b""
        else:
            token_b = token.encode("utf-8")
        msg_b = msg.encode("utf-8")

        header = (
            len(room_name_b).to_bytes(1, "big")
            + len(token_b).to_bytes(1, "big")
        )

        return header + room_name_b + token_b + msg_b


# -------------------------------
# プロトコル外の共通処理
# -------------------------------
class SocketHelper:
    @staticmethod
    def recv_exact(sock, size):
        data = b""
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError(
                    f"Connection closed before receiving expected bytes "
                    f"(excepted: {size} byte, received: {len(data)} byte)"
                )
            data += chunk
        return data