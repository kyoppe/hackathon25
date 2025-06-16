# Slack +g Bot

SlackのEvent APIを使用して、`@user +g`のようなメッセージを検出し、ログに記録するFlaskアプリケーションです。

## セットアップ

1. Python 3.9以上をインストール
2. 仮想環境を作成して有効化:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linuxの場合
   # または
   .\venv\Scripts\activate  # Windowsの場合
   ```
3. 依存パッケージをインストール:
   ```bash
   pip install -r requirements.txt
   ```
4. `.env`ファイルを作成:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   SLACK_SIGNING_SECRET=your_signing_secret_here
   ```

## 実行方法

1. 仮想環境を有効化:
   ```bash
   source venv/bin/activate
   ```
2. アプリケーションを起動:
   ```bash
   python app.py
   ```

## ローカルテスト

1. ngrokをインストール
2. 別のターミナルでngrokを起動:
   ```bash
   ngrok http 5000
   ```
3. ngrokのURLをSlackアプリのEvent Subscriptionsに設定

## デプロイ

1. コードをGitリポジトリにプッシュ
2. EC2インスタンスで:
   ```bash
   git pull
   source venv/bin/activate
   python app.py
   ```

## 機能

- `/slack/events`エンドポイントでSlackイベントを受け取る
- `app_mention`と`message.channels`イベントを処理
- `<@ユーザーID> +g`パターンを検出
- 投稿者と加点された相手をログに出力 