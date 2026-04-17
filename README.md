# 🐾 OpenClaw Watchdog - 智能看门狗

> 多模型自动切换 + 飞书告警，借鉴 Claude Code 架构设计

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## ⚠️ 安全警告

> **所有 API Key 和 Webhook 地址禁止上传到任何公共仓库！**
> 
> 上传前请务必替换为环境变量或占位符，防止信息泄露。

---

## 🎯 功能特性

### 模型看门狗（model_watchdog.py）
- **多模型支持**：MiniMax / DeepSeek 自动切换
- **智能切换**：连续失败3次自动切换到备用模型
- **恢复检测**：主模型恢复时自动通知
- **飞书告警**：重要事件实时推送

### 进程看门狗（watchdog.sh）
- **进程保活**：检测 OpenClaw 进程，异常自动重启
- **端口清理**：解决端口占用导致的启动失败
- **飞书通知**：重启成功/失败实时告警

---

## 🏗️ 架构设计

借鉴 Claude Code 512K 源码泄露事件中的看门狗设计理念：

```
模型异常 → 失败计数 → 3次失败 → 自动切换 → 飞书通知
                                        ↓
进程消失 → 端口清理 → 自动重启 → 通知结果
```

---

## 🚀 快速开始

### 1. 配置 API Key

**方式一：环境变量（推荐）**
```bash
export MINIMAX_KEY="your-minimax-key"
export DEEPSEEK_KEY="your-deepseek-key"
export FEISHU_WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-id"
```

**方式二：直接修改脚本中的常量**

### 2. 设置定时任务

```bash
# 每5分钟检测模型状态
*/5 * * * * python3 /path/to/model_watchdog.py

# 每10分钟检测进程状态
*/10 * * * * bash /path/to/watchdog.sh
```

---

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `model_watchdog.py` | 模型看门狗 - 多模型自动切换 |
| `watchdog.sh` | 进程看门狗 - 进程保活 |
| `README.md` | 说明文档 |

---

## 🔧 依赖

- Python 3.8+
- curl
- OpenClaw
- 飞书群 Webhook

---

## 📄 License

MIT License
