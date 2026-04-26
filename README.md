# Online Chat Messenger
CLI上で実行可能なチャットシステムです。

## 機能
- ルームの作成/参加, ユーザー登録：
  - リクエストの確実な受信と順序の保証を要するため、TCP通信で行います。
  - 登録に成功したユーザーにはトークンが与えられ、以降の認証に用いられます。
- ルーム内でのチャット：
  - リアルタイム性が重視されるため、UDP通信で行います。
  - 作成/参加したルーム単位で、複数のクライアントがメッセージのやり取りを行うことができます。
  - ルームの作成者が退出すると、ルームが自動的に削除されます。

## 実行方法
1. サーバを起動
```
python3 server.py
```

2. 別ターミナルでクライアントを起動
```
python3 client.py
```

3. 操作コード
  - ルームを作成: `1`
  - ルームに参加: `2`
  - システムを終了: `0`
```
> Operation (1 or 2 or 0): 
```

4. 作成もしくは参加するチャットルームの名前を入力。
```
> Room name: 
```

5. ユーザーネームを入力
```
> User name: 
```

6. UDP接続に切り替わり、対象のルームでチャットが開始します。

> Ctrl + C 割り込みで終了することができます。

## 動作環境
- Python3.8以上
- CLI

## 使用技術
- Python
  - socket(AF_INET)
  - threading
  - secrets
  - json

## 開発メンバー
- <a href="https://github.com/wmelon89">wmelon89</a>
- <a href="https://github.com/kokinomu-blip">kokinomu-blip</a>
- <a href="https://github.com/Nonnok">Nonnok</a>