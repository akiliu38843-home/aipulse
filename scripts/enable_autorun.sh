#!/bin/bash
# 启动 AIPulse 每日定时任务（工作日 09:30 自动抓取+构建）
PLIST="$HOME/Library/LaunchAgents/com.user.ainative.daily.plist"
if launchctl list 2>/dev/null | grep -q "com.user.ainative.daily"; then
    echo "检测到已有旧版本，先卸载..."
    launchctl unload "$PLIST" 2>/dev/null || true
fi
launchctl load "$PLIST" && \
    echo "✅ AIPulse 定时任务已启动（工作日 09:30）" && \
    echo "   日志: $(dirname "$0")/../logs/" && \
    echo "   停用: bash $(dirname "$0")/disable_autorun.sh" || \
    echo "❌ 启动失败，请检查 plist 路径: $PLIST"
