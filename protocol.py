# プロトコル担当：Nonnok

# -------------------------------
# TCRP (Chat room protocol / TCP)
# -------------------------------
class TCRP:
    HEADER_SIZE = 32

    def recv_packet(sock):
        """
        TCPパケットを受信し、内容を解析する。

        処理内容:
        - ヘッダを固定長で受信
        - ヘッダから以下を取得
            - room_nameの長さ
            - operation
            - state
            - payloadの長さ
        - ボディを受信
        - room_nameとpayloadをデコード

        戻り値:
        - (operation, state, room_name, payload)
        """
        pass

    def parse_header(header):
        """
        ヘッダ部分を解析する。

        内容:
        - 1byte : room_name長
        - 1byte : operation
        - 1byte : state
        - 29byte: payload長

        戻り値:
        - (room_name_len, operation, state, payload_len)
        """
        pass

    def parse_body(body, room_name_len, payload_len):
        """
        ボディ部分を解析する。

        処理内容:
        - 前半をroom_nameとしてデコード
        - 後半をpayloadとしてデコード

        戻り値:
        - (room_name, payload)
        """
        pass

    def send_packet(sock, room_name, operation, state, payload):
        """
        TCPパケットを生成して送信する。

        処理内容:
        - room_nameとpayloadをバイト列に変換
        - ヘッダを生成
          フォーマット:
          - room_name_len : 1byte
          - operation     : 1byte
          - state         : 1byte
          - payload_len   : 29byte (big endian)
        - ヘッダ + ボディを送信
        """
        pass


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