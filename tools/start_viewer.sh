#!/bin/bash

# 切换到 JSON 文件所在目录
cd ~/Library/Application\ Support/Stats/

# 启动 Python HTTP 服务器并在 2 秒后打开浏览器
echo "启动流量查看器..."
echo "访问地址: http://localhost:8765/traffic_viewer.html"
echo "按 Ctrl+C 停止服务器"

# 在后台打开浏览器
sleep 1 && open "http://localhost:8765/traffic_viewer.html" &

# 启动服务器
python3 -m http.server 8765
