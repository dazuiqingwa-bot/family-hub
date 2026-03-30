#!/usr/bin/env python3
"""
直接通过飞书 API 给指定用户发消息（主动推送，不依赖 OpenClaw delivery）。

用法：
  python3 feishu-send.py <open_id> <消息内容>

示例：
  python3 feishu-send.py ou_216a3f71ce740715ecb08de972fb0749 "你好，禾禾！"

需要 openclaw.json 里配置了 feishu appId / appSecret。
"""

import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"

def load_feishu_creds(account_id: str = "default"):
    cfg = json.loads(OPENCLAW_CONFIG.read_text())
    accounts = cfg["channels"]["feishu"]["accounts"]
    if account_id not in accounts:
        raise RuntimeError(f"账号 {account_id} 不存在于 openclaw.json")
    acc = accounts[account_id]
    return acc["appId"], acc["appSecret"]

def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data}")
    return data["tenant_access_token"]

def send_message(token: str, open_id: str, text: str):
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    payload = json.dumps({
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}),
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if data.get("code") != 0:
        raise RuntimeError(f"发送失败: {data}")
    return data

def main():
    if len(sys.argv) < 3:
        print("用法: python3 feishu-send.py <open_id> <消息内容>")
        sys.exit(1)

    open_id = sys.argv[1]
    text = " ".join(sys.argv[2:])
    # 把字面的 \n 转成真正的换行符
    text = text.replace('\\n', '\n')

    # 支持 --account 参数指定飞书账号，默认 default
    account_id = "default"
    if "--account" in sys.argv:
        idx = sys.argv.index("--account")
        account_id = sys.argv[idx + 1]

    app_id, app_secret = load_feishu_creds(account_id)
    token = get_tenant_access_token(app_id, app_secret)
    result = send_message(token, open_id, text)
    print(f"✅ 发送成功，message_id: {result['data']['message_id']}")

if __name__ == "__main__":
    main()
