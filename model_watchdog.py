#!/usr/bin/env python3
"""
模型看门狗 - Model Watchdog
借鉴 Claude Code 架构设计

功能：
- 多模型自动切换（MiniMax / DeepSeek）
- 失败计数 + 连续3次触发切换
- 恢复检测 + 自动通知
- 飞书群实时告警

使用方式：
    python3 model_watchdog.py

配置（环境变量或直接修改下面的常量）：
    FEISHU_WEBHOOK  - 飞书群 Webhook 地址
    MINIMAX_KEY     - MiniMax API Key
    DEEPSEEK_KEY    - DeepSeek API Key
"""

import urllib.request
import json
import subprocess
import os
from datetime import datetime

# ========== 配置区（请修改为你的配置）==========

# 飞书群 Webhook
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID")

# MiniMax 配置
MINIMAX = {
    "url": "https://api.minimaxi.com/anthropic/v1/messages",
    "key": os.environ.get("MINIMAX_KEY", "YOUR_MINIMAX_API_KEY")
}

# DeepSeek 配置
DEEPSEEK = {
    "url": "https://api.deepseek.com/chat/completions",
    "key": os.environ.get("DEEPSEEK_KEY", "YOUR_DEEPSEEK_API_KEY")
}

# OpenClaw 配置文件路径
CONFIG = os.environ.get("OPENCLAW_CONFIG", "/root/.openclaw/openclaw.json")

# 日志文件
LOG = "/root/.openclaw/workspace/memory/model_watchdog.log"

# 失败计数文件
FAIL_COUNT_FILE = "/root/.openclaw/workspace/memory/model_fail_count.json"

# ========== 以下为核心逻辑，不需要修改 ==========

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = "[%s] %s" % (ts, msg)
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def send_feishu(text, webhook=None):
    """发送飞书通知"""
    webhook = webhook or FEISHU_WEBHOOK
    payload = json.dumps({"msg_type": "text", "content": {"text": text}}, ensure_ascii=False)
    try:
        subprocess.run(
            ["curl", "-s", "-X", "POST", webhook, "-H", "Content-Type: application/json", "-d", payload],
            capture_output=True, timeout=10
        )
        log(f"飞书通知已发送: {text[:50]}...")
    except Exception as e:
        log(f"飞书通知失败: {str(e)}")

def send_alert(title, content):
    msg = f"🤖 模型监控告警\n\n📌 {title}\n\n{content}\n\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_feishu(msg)

def test_api(model_cfg):
    """测试某个 API 是否可用"""
    try:
        data = json.dumps({
            "model": "auto" if "minimaxi" in model_cfg["url"] else "deepseek-chat",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "hi"}]
        }).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + model_cfg["key"]
        }
        if "minimaxi" in model_cfg["url"]:
            headers["anthropic-version"] = "2023-06-01"
        req = urllib.request.Request(model_cfg["url"], data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:
        log(f"检测失败: {str(e)}")
        return False

def get_fail_count():
    if not os.path.exists(FAIL_COUNT_FILE):
        return {"minimax": 0, "deepseek": 0}
    try:
        with open(FAIL_COUNT_FILE) as f:
            return json.load(f)
    except:
        return {"minimax": 0, "deepseek": 0}

def save_fail_count(data):
    with open(FAIL_COUNT_FILE, "w") as f:
        json.dump(data, f)

def get_current_model():
    try:
        with open(CONFIG) as f:
            cfg = json.load(f)
        return cfg.get("agents", {}).get("defaults", {}).get("model", {}).get("primary", "minimax/auto")
    except:
        return "minimax/auto"

def switch_to(model_name, label):
    """切换主模型"""
    try:
        with open(CONFIG) as f:
            cfg = json.load(f)
        cfg.setdefault("agents", {}).setdefault("defaults", {}).setdefault("model", {})["primary"] = model_name
        with open(CONFIG, "w") as f:
            json.dump(cfg, f)
        log(f"已切换到 {label} ({model_name})")
        send_alert(f"模型自动切换: {label}", f"检测到主模型异常，已自动切换到 {model_name}")
        subprocess.run(["openclaw", "gateway", "restart"], capture_output=True, timeout=30)
        return True
    except Exception as e:
        log(f"切换失败: {str(e)}")
        send_alert("模型切换失败", f"尝试切换到 {model_name} 失败: {str(e)}")
        return False

def main():
    log("=== 模型看门狗启动 ===")
    current = get_current_model()
    fail = get_fail_count()
    log(f"当前主模型: {current} 失败计数: minimax={fail['minimax']} deepseek={fail['deepseek']}")

    is_deepseek = "deepseek" in current
    test_fn = lambda: test_api(DEEPSEEK) if is_deepseek else test_api(MINIMAX)
    model_key = "deepseek" if is_deepseek else "minimax"
    other_fn = lambda: test_api(MINIMAX) if is_deepseek else test_api(DEEPSEEK)
    other_key = "minimax" if is_deepseek else "deepseek"

    if test_fn():
        if fail[model_key] > 0:
            send_alert(f"{label_map[model_key]} 恢复", f"{label_map[model_key]} 模型已恢复正常")
            log(f"{model_key} 恢复")
        fail[model_key] = 0
        save_fail_count(fail)
        log(f"{model_key} 正常")
    else:
        fail[model_key] += 1
        save_fail_count(fail)
        log(f"{model_key} 失败 {fail[model_key]}/3")
        
        label_map = {"minimax": "MiniMax", "deepseek": "DeepSeek"}
        if fail[model_key] == 1:
            send_alert(f"{label_map[model_key]} 异常", f"{label_map[model_key]} 模型检测失败 1/3，等待下次检测...")
        elif fail[model_key] >= 3:
            send_alert(f"{label_map[model_key]} 连续失败", f"{label_map[model_key]} 模型连续失败 {fail[model_key]} 次，准备切换...")
            if other_fn():
                other_model = "minimax/auto" if not is_deepseek else "deepseek/deepseek-chat"
                switch_to(other_model, label_map[other_key])
            else:
                log("两个模型都挂了")
                send_alert("模型告警", f"{label_map[model_key]} 和 {label_map[other_key]} 都不可用")

    log("=== 模型看门狗完成 ===")

if __name__ == "__main__":
    main()
