#!/bin/bash
# OpenClaw 进程看门狗
# 借鉴 Claude Code 守护进程设计
# 功能：检测 OpenClaw 进程，异常消失时自动重启 + 飞书告警

# ========== 配置区 ==========
PORT=18789
MAX_IDLE_MIN=10
LOG="/root/.openclaw/workspace/memory/watchdog.log"
FEISHU_WEBHOOK="${FEISHU_WEBHOOK:-https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_WEBHOOK_ID}"

# ========== 逻辑 ==========
send_alert() {
    curl -s -X POST "$FEISHU_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"🤖 OpenClaw 看门狗告警\n\n\$1\"}}" > /dev/null
}

DATE=$(date '+%Y-%m-%d %H:%M')

if pgrep -f "openclaw" > /dev/null 2>&1; then
    echo "[$DATE] ✅ OpenClaw 进程正常" >> "$LOG"
    exit 0
fi

echo "[$DATE] ⚠️ OpenClaw 进程消失，触发看门狗" >> "$LOG"
send_alert "OpenClaw 进程消失，正在重启..."

fuser -k ${PORT}/tcp 2>/dev/null
sleep 2
pkill -f "openclaw" 2>/dev/null
sleep 1

cd /root/.openclaw && nohup openclaw gateway start > /root/.openclaw/workspace/memory/gateway-restart.log 2>&1 &
sleep 5

if pgrep -f "openclaw" > /dev/null 2>&1; then
    echo "[$DATE] ✅ OpenClaw 重启成功" >> "$LOG"
    send_alert "OpenClaw 已自动重启恢复正常"
else
    echo "[$DATE] ❌ OpenClaw 重启失败" >> "$LOG"
    send_alert "⚠️ OpenClaw 重启失败，请手动检查！"
fi
