#!/bin/bash
set -e

APP_NAME="TrafficViewer"
APP_DIR="$HOME/Applications/$APP_NAME.app"
BUNDLE_ID="com.yg520.traffic-viewer"
LAUNCH_AGENT_PLIST="$HOME/Library/LaunchAgents/$BUNDLE_ID.plist"

echo "=== 卸载 TrafficViewer 菜单栏应用 ==="
echo ""

# 停止 LaunchAgent
if [ -f "$LAUNCH_AGENT_PLIST" ]; then
    echo "停止服务..."
    launchctl unload "$LAUNCH_AGENT_PLIST" 2>/dev/null || true
    rm -f "$LAUNCH_AGENT_PLIST"
    echo "已删除 LaunchAgent 配置"
else
    echo "未找到 LaunchAgent 配置（跳过）"
fi

# 删除 .app
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo "已删除应用: $APP_DIR"
else
    echo "未找到应用（跳过）"
fi

echo ""
echo "=== 卸载完成 ==="
