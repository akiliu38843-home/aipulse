#!/bin/bash
# 停止 AIPulse 每日定时任务
PLIST="$HOME/Library/LaunchAgents/com.user.ainative.daily.plist"
if launchctl list 2>/dev/null | grep -q "com.user.ainative.daily"; then
    launchctl unload "$PLIST" && echo "✅ AIPulse 定时任务已停用"
else
    echo "ℹ️  AIPulse 定时任务未在运行"
fi
