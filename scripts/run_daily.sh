#!/bin/bash
# AIPulse 每日自动抓取 + 构建脚本
# 仅工作日执行（周一到周五），由 launchd 每天 09:30 触发
# 手动测试：bash scripts/run_daily.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/daily_$(date +%Y%m%d).log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

# ── 工作日检查（1=Mon … 5=Fri，6=Sat，7=Sun）──
DOW=$(date +%u)
if [ "$DOW" -gt 5 ]; then
    log "周末（DOW=$DOW），跳过。"
    exit 0
fi

log "=== AIPulse 每日抓取开始 ($(date '+%A %Y-%m-%d')) ==="

# ── 代理设置（7897，本机唯一出口）──
export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897

# ── 读取 DeepSeek API Key（从 ~/.ainative_env 优先，其次当前 env）──
ENV_FILE="$HOME/.ainative_env"
if [ -f "$ENV_FILE" ]; then
    # 只 source 形如 KEY=VALUE 的行，不执行任意代码
    while IFS='=' read -r k v; do
        [[ "$k" =~ ^[A-Z_]+$ ]] && export "$k=$v"
    done < <(grep -v '^#' "$ENV_FILE" | grep '=')
    log "已从 $ENV_FILE 加载环境变量"
fi

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    log "WARN: DEEPSEEK_API_KEY 未设置 — 翻译将回落到原文英语"
fi

cd "$BASE_DIR"
log "工作目录: $BASE_DIR"

log "--- fetch_newsletters.py ---"
/usr/bin/python3 fetch_newsletters.py 2>&1 | tee -a "$LOG"

log "--- build_news.py zh ---"
/usr/bin/python3 build_news.py zh 2>&1 | tee -a "$LOG"

log "=== 完成 ==="
