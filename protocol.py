# プロトコル担当：Nonnok

# -------------------------------
# TCRP (Chat room protocol / TCP)
# -------------------------------
class TCRP:
    HEADER_SIZE = 32

    OPERATION = {
    "create_room": 1,
    "join_room": 2,
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
        payload = body[room_name_len:].decode("utf-8")

        return room_name, payload

    # TCPパケットを生成して送信する。
    @classmethod
    def send_packet(self, sock, room_name, operation, state, payload):
        room_name_b = room_name.encode("utf-8")

        if payload is None:
            header = self.build_header(len(room_name_b), operation, state, 0)
            body = room_name_b
        else:
            payload_b = payload.encode("utf-8")
            header = self.build_header(len(room_name_b), operation, state, len(payload_b))
            body = room_name_b + payload_b

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
    def parse_packet(data):
        """
        UDPパケットを解析する。

        フォーマット:
        - 1byte : room_name長
        - 1byte : token長
        - 可変 : room_name
        - 可変 : token
        - 残り : メッセージ

        処理内容:
        - 各フィールドを切り出し
        - UTF-8でデコード

        戻り値:
        - (room_name, token, message)
        """
        pass

    def build_packet(room_name, token, msg):
        """
        UDPパケットを生成する。

        処理内容:
        - 各データをバイト列に変換
        - ヘッダを生成
          フォーマット:
          - room_name長 : 1byte
          - token長     : 1byte
        - ヘッダ + room_name + token + message を結合

        戻り値:
        - bytes
        """
        pass


# -------------------------------
# プロトコル外の共通処理
# -------------------------------
class SocketHelper:
    @staticmethod
    def recv_exact(sock, size):
        """
        指定されたサイズ分のデータを確実に受信する。

        処理内容:
        - sock.recvを繰り返し呼び出し、sizeバイト分取得する
        - 途中で接続が切れた場合は例外を投げる

        用途:
        - TCPでの固定長データ受信に使用
        """
        pass