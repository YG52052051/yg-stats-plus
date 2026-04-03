#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="TrafficViewer"
APP_DIR="$HOME/Applications/$APP_NAME.app"
BUNDLE_ID="com.yg520.traffic-viewer"
LAUNCH_AGENT_PLIST="$HOME/Library/LaunchAgents/$BUNDLE_ID.plist"

echo "=== TrafficViewer 菜单栏应用安装 ==="
echo ""

# 检查 swift 编译器
if ! command -v swiftc &> /dev/null; then
    echo "错误: 未找到 swiftc，请先安装 Xcode Command Line Tools:"
    echo "  xcode-select --install"
    exit 1
fi

# 检查 python3
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

echo "[1/5] 编译 Swift 应用..."
BUILD_DIR=$(mktemp -d)
swiftc -o "$BUILD_DIR/$APP_NAME" \
    "$SCRIPT_DIR/traffic_bar.swift" \
    -framework Cocoa \
    -suppress-warnings

echo "[2/5] 创建 .app 包..."
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# 复制二进制文件
cp "$BUILD_DIR/$APP_NAME" "$APP_DIR/Contents/MacOS/"

# 复制 HTML 资源到包内
cp "$SCRIPT_DIR/traffic_viewer.html" "$APP_DIR/Contents/Resources/"

# 创建 Info.plist（LSUIElement=true 隐藏 Dock 图标）
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>TrafficViewer</string>
    <key>CFBundleIdentifier</key>
    <string>com.yg520.traffic-viewer</string>
    <key>CFBundleName</key>
    <string>TrafficViewer</string>
    <key>CFBundleDisplayName</key>
    <string>Traffic Viewer</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
</dict>
</plist>
EOF

echo "[3/5] 配置 LaunchAgent（开机自启）..."
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$LAUNCH_AGENT_PLIST" << AGENTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$BUNDLE_ID</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_DIR/Contents/MacOS/$APP_NAME</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
AGENTEOF

echo "[4/5] 加载 LaunchAgent..."
# 先卸载已有的（忽略错误）
launchctl unload "$LAUNCH_AGENT_PLIST" 2>/dev/null || true
# 等待旧进程退出
sleep 1
# 加载新的
launchctl load "$LAUNCH_AGENT_PLIST"

echo "[5/5] 清理..."
rm -rf "$BUILD_DIR"

echo ""
echo "=== 安装完成！==="
echo ""
echo "  应用位置:  $APP_DIR"
echo "  自启配置:  $LAUNCH_AGENT_PLIST"
echo ""
echo "菜单栏应该已出现网络图标 (📶 风格)"
echo "  - 点击图标 → 「打开流量查看器」"
echo "  - 访问地址: http://localhost:8765/traffic_viewer.html"
echo ""
echo "管理命令:"
echo "  停止服务:  launchctl unload $LAUNCH_AGENT_PLIST"
echo "  启动服务:  launchctl load $LAUNCH_AGENT_PLIST"
echo "  完全卸载:  bash $SCRIPT_DIR/uninstall_auto_start.sh"
echo ""
echo "提示: 更新 HTML 后重新运行此脚本即可"
