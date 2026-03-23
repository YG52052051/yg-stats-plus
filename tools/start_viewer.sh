#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR=~/Library/Application\ Support/Stats

# 确保 Stats 数据目录存在
mkdir -p "$DATA_DIR"

# 复制 HTML 文件到数据目录（这样 JSON 和 HTML 在同一目录）
cp "$SCRIPT_DIR/traffic_viewer.html" "$DATA_DIR/"

echo "启动流量查看器..."
echo "访问地址: http://localhost:8765/traffic_viewer.html"
echo "按 Ctrl+C 停止服务器"

# 在后台打开浏览器
sleep 1 && open "http://localhost:8765/traffic_viewer.html" &

# 切换到数据目录并启动服务器
cd "$DATA_DIR"
python3 -m http.server 8765
