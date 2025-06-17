import json
import os
import re
import requests
from datetime import datetime
import logging

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants（環境変数から読み込み）
MAX_PLUS_POINTS = int(os.getenv('MAX_PLUS_POINTS', 10))
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
DD_API_KEY = os.getenv('DD_API_KEY')
DD_SITE = os.getenv('DD_SITE', 'datadoghq.com')

# 環境変数の検証
if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")
if not DD_API_KEY:
    raise ValueError("DD_API_KEY environment variable is required")

def send_datadog_metric(metric_name, value, tags=None):
    url = f"https://api.{DD_SITE}/api/v2/series"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "DD-API-KEY": DD_API_KEY
    }
    payload = {
        "series": [
            {
                "metric": metric_name,
                "type": 0,
                "points": [
                    {
                        "timestamp": int(datetime.utcnow().timestamp()),
                        "value": value
                    }
                ],
                "tags": tags or []
            }
        ]
    }
    logger.info(f"Sending metric to Datadog: {json.dumps(payload, indent=2)}")
    response = requests.post(url, headers=headers, json=payload)
    logger.info(f"Datadog API response: {response.status_code} - {response.text}")
    return response.ok

def get_user_info(user_id):
    try:
        response = requests.get(
            "https://slack.com/api/users.info",
            params={"user": user_id},
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        )
        data = response.json()
        logger.info(f"User info API response: {json.dumps(data)}")
        if data.get("ok"):
            return data["user"]["real_name"]
        else:
            logger.error(f"Failed to get user info: {data.get('error')}")
            return user_id
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return user_id

def get_channel_info(channel_id):
    try:
        response = requests.get(
            "https://slack.com/api/conversations.info",
            params={"channel": channel_id},
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
        )
        data = response.json()
        logger.info(f"Channel info API response: {json.dumps(data)}")
        if data.get("ok"):
            return data["channel"]["name"]
        else:
            logger.error(f"Failed to get channel info: {data.get('error')}")
            return channel_id
    except Exception as e:
        logger.error(f"Error getting channel info: {str(e)}")
        return channel_id

def extract_user_ids(text):
    return re.findall(r'<@([A-Z0-9]+)>', text)

def extract_numeric_value(text):
    match = re.search(r'\+(\d+)', text)
    return int(match.group(1)) if match else None

def lambda_handler(event, context):
    logger.info(f"Raw event: {json.dumps(event)}")

    # bodyをパース（HTTP API 経由の場合）
    if "body" in event:
        try:
            body = json.loads(event["body"])
        except Exception as e:
            logger.error(f"Failed to parse event['body']: {str(e)}")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "invalid body"})
            }
    else:
        body = event  # テスト実行やローカル動作時

    # SlackのURL検証イベント
    if body.get("type") == "url_verification":
        challenge = body.get("challenge")
        logger.info(f"Responding to Slack challenge: {challenge}")
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"challenge": challenge})
        }

    # Slackのイベントコールバック処理
    if body.get("type") == "event_callback":
        slack_event = body.get("event", {})

        if slack_event.get("type") == "message" and "subtype" not in slack_event:
            text = slack_event.get("text", "")
            user_ids = extract_user_ids(text)
            numeric_value = extract_numeric_value(text)

            if len(user_ids) == 1 and numeric_value is not None:
                if numeric_value > MAX_PLUS_POINTS:
                    logger.warning(f"Value {numeric_value} exceeds max ({MAX_PLUS_POINTS}). Adjusting.")
                    numeric_value = MAX_PLUS_POINTS

                sender_id = slack_event.get("user")
                receiver_id = user_ids[0]
                channel_id = slack_event.get("channel")

                sender_name = get_user_info(sender_id)
                receiver_name = get_user_info(receiver_id)
                channel_name = get_channel_info(channel_id)

                logger.info(f"Plus points: {sender_name} -> {receiver_name}: +{numeric_value} in {channel_name}")

                metric_name = "test.hackathon.recognidog.points"
                tags = [
                    "env:hackathon",
                    f"sender:{sender_name}",
                    f"receiver:{receiver_name}",
                    f"channel:{channel_name}"
                ]

                if send_datadog_metric(metric_name, numeric_value, tags):
                    logger.info("Metric successfully sent to Datadog.")
                else:
                    logger.error("Failed to send metric to Datadog.")

                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "message": "Plus points event processed",
                        "sender": sender_name,
                        "receiver": receiver_name,
                        "points": numeric_value,
                        "channel": channel_name
                    })
                }

    # 処理対象外の場合
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Event received but not processed"})
    }
