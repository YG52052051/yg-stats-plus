# Stats

<a href="https://github.com/YG52052051/yg-stats-plus/releases"><p align="center"><img src="https://github.com/exelban/stats/raw/master/Stats/Supporting%20Files/Assets.xcassets/AppIcon.appiconset/icon_256x256.png" width="120"></p></a>

macOS 菜单栏系统监控工具

## 安装

### 从 GitHub Actions 下载
1. 访问 [Actions](https://github.com/YG52052051/yg-stats-plus/actions) 页面
2. 点击最新的成功构建
3. 在 "Artifacts" 区域下载 `Stats-macOS`
4. 解压后右键点击 `Stats.app` → 打开（首次启动）

### Homebrew（原版）
```bash
brew install stats
```

## 系统要求

- macOS 14.0 (Sonoma) 或更高版本

## 功能特性

Stats 是一款 macOS 系统监控应用，可以在菜单栏显示各种系统信息：

- **CPU** - 利用率、温度、频率
- **GPU** - 利用率、温度
- **内存** - 使用情况、压力
- **磁盘** - 读写速度、容量
- **网络** - 带宽、连接状态
- **电池** - 电量、健康度
- **传感器** - 温度、电压、功率
- **蓝牙** - 设备连接状态
- **时钟** - 多时区显示

## 🆕 新增功能：进程流量历史记录

### 功能说明
记录每个应用的网络流量使用情况，支持历史趋势查看。

**特点：**
- **后台持续记录** - 无需打开 popup 窗口，流量数据会在后台自动采集
- 按 **10分钟** 粒度记录流量数据
- 每 **5分钟** 自动保存
- 支持查看任意时间段的历史数据
- **趋势图** 可视化展示流量变化
- **关键字搜索** - 快速查找特定进程
- **时间范围筛选** - 按时间段过滤数据

### 数据文件位置
```
~/Library/Application Support/Stats/traffic_history.json
```

### 查看流量数据

1. **打开 HTML 查看器**
   ```
   tools/traffic_viewer.html
   ```

2. **拖拽 JSON 文件** 到网页中

3. **功能说明**
   - 📊 统计卡片：显示总下载/上传/流量/进程数
   - 📅 日期筛选：按日期过滤数据
   - 🔍 关键字搜索：快速查找进程
   - 📈 趋势图：点击进程名称查看流量趋势（最多5个）
   - 📋 排行榜：按流量使用量排序

### 数据结构示例
```json
{
  "2026-03-20": {
    "19:20": {
      "微信_1275": {"name": "微信", "pid": 1275, "download": 50000000, "upload": 10000000}
    },
    "19:30": {
      "微信_1275": {"name": "微信", "pid": 1275, "download": 30000000, "upload": 5000000}
    }
  }
}
```

### 数据说明
- **增量存储**：每个时间槽存储的是该 10 分钟内的流量增量（bytes）
- **自动聚合**：HTML 查看器会自动计算选定时间范围内的总累计值
- **所有进程**：记录所有有网络活动的进程（不限制数量）
- **进程标识**：使用 `进程名_PID` 作为唯一标识（同一进程重启后 PID 会变化）
- **后台采集**：流量数据在后台持续采集，即使 popup 窗口关闭也不会中断

## 🔄 与原版的区别

- ✅ **禁用自动更新** - 不会自动下载安装官方版本
- ✅ **后台流量记录** - 持续记录进程流量，无需手动打开窗口

## 常见问题

### 如何调整菜单栏图标顺序？
macOS 决定菜单栏图标的顺序：
1. 按住 ⌘ (Command 键)
2. 拖动图标到想要的位置
3. 松开 ⌘

### 如何降低 CPU 占用？
最耗资源的模块是 **传感器** 和 **蓝牙**。禁用这些模块可以显著降低 CPU 占用。

### 应用崩溃怎么办？
1. 确保使用最新版本
2. 查看 [Issues](https://github.com/YG52052051/yg-stats-plus/issues) 是否有相关问题

## 支持的语言

- 简体中文
- 繁体中文
- English
- 日本語
- 한국어
- Русский
- Українська
- Polski
- Deutsch
- Français
- Español
- Italiano
- Português
- 等更多...

## 许可证

[MIT License](LICENSE)

## 致谢

本项目基于 [exelban/stats](https://github.com/exelban/stats) 开发，感谢原作者的贡献。
