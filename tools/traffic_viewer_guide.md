# Traffic Viewer 菜单栏应用

macOS 状态栏应用，开机自动启动 HTTP 服务器，通过浏览器查看网络流量数据。

## 功能

- 开机/登录自动启动，无需手动操作
- 状态栏显示网络图标，鼠标悬停可查看运行状态
- 点击图标打开菜单，可快速访问流量查看器
- 纯菜单栏应用，不占用 Dock 位置

## 快速开始

### 安装

```bash
cd ~/cc_project/yg-stats-plus
bash tools/install_auto_start.sh
```

安装完成后，菜单栏会出现网络图标，服务自动运行。

### 卸载

```bash
bash tools/uninstall_auto_start.sh
```

## 使用

安装后无需任何操作，每次开机会自动启动。

点击菜单栏网络图标，选择「打开流量查看器」即可在浏览器中查看流量数据。

访问地址：`http://localhost:8765/traffic_viewer.html`

## 管理命令

```bash
# 停止服务
launchctl unload ~/Library/LaunchAgents/com.yg520.traffic-viewer.plist

# 启动服务
launchctl load ~/Library/LaunchAgents/com.yg520.traffic-viewer.plist

# 查看服务状态
launchctl list | grep traffic-viewer
```

也可以通过菜单栏图标操作：
- 「重启服务」— 重新启动 HTTP 服务器
- 「退出」— 关闭应用（下次登录会自动重新启动）

## 更新流量查看器页面

修改 `tools/traffic_viewer.html` 后，重新运行安装脚本即可更新：

```bash
bash tools/install_auto_start.sh
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `traffic_bar.swift` | Swift 菜单栏应用源码 |
| `traffic_viewer.html` | 流量查看器网页 |
| `install_auto_start.sh` | 安装脚本（编译 + 配置自启） |
| `uninstall_auto_start.sh` | 卸载脚本 |
| `start_viewer.sh` | 手动启动脚本（无需菜单栏应用时使用） |

## 安装位置

| 项目 | 路径 |
|------|------|
| 应用 | `~/Applications/TrafficViewer.app` |
| 自启配置 | `~/Library/LaunchAgents/com.yg520.traffic-viewer.plist` |
| 流量数据 | `~/Library/Application Support/Stats/` |

## 图标状态

| 图标 | 含义 |
|------|------|
| 网络图标（正常） | HTTP 服务器运行中 |
| 感叹号三角形 | 服务器未运行（可点击「重启服务」） |

## 故障排除

**菜单栏没有图标**
```bash
# 检查服务是否加载
launchctl list | grep traffic-viewer
# 手动启动
launchctl load ~/Library/LaunchAgents/com.yg520.traffic-viewer.plist
```

**页面打不开**
- 确认 python3 可用：`which python3`
- 重启服务：点击菜单栏图标 → 「重启服务」

**端口被占用**
- 检查占用：`lsof -i :8765`
- 关闭旧进程后重启服务
