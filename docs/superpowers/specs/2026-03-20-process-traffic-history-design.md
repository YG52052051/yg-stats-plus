# 进程流量历史记录功能设计

## 概述

为 Stats 应用的网络模块添加进程级流量历史记录功能。该功能将记录每个应用/进程的上传和下载流量，按小时聚合存储到 LevelDB 中，便于后续分析和查看。

## 目标

- 记录每个进程的网络流量历史数据
- 按小时聚合存储，支持查看今日/近7天/近30天的数据
- 不修改现有 UI，只做数据存储层
- 数据格式易于外部工具读取

## 非目标

- 不修改现有 UI 界面
- 不添加应用内查看历史的功能（由外部工具实现）
- 不支持分钟级别的细粒度数据

## 技术方案

### 数据存储

复用现有 `DB.shared` (LevelDB) 存储基础设施。

**Key 格式**：
```
process_traffic|{YYYY-MM-DD}|{HH}
```
示例：`process_traffic|2026-03-20|14` 表示 2026年3月20日 14:00-15:00 的数据

**Value 格式**（JSON 字符串）：
```json
{
  "Safari_12345": {"name": "Safari", "pid": 12345, "download": 1234567, "upload": 234567},
  "Slack_67890": {"name": "Slack", "pid": 67890, "download": 567890, "upload": 12345},
  "com.apple.WebKit.Networking_54321": {"name": "com.apple.WebKit.Networking", "pid": 54321, "download": 987654, "upload": 45678}
}
```

### 数据结构定义

在 `Modules/Net/readers.swift` 中新增结构体：

```swift
struct ProcessTrafficRecord: Codable {
    let name: String      // 进程名称
    let pid: Int          // 进程 ID
    var download: Int64 = 0
    var upload: Int64 = 0
}

typealias ProcessTrafficBucket = [String: ProcessTrafficRecord]  // key: "{name}_{pid}"
```

**更新后的 Value 格式**（JSON 字符串）：
```json
{
  "Safari_12345": {"name": "Safari", "pid": 12345, "download": 1234567, "upload": 234567},
  "Slack_67890": {"name": "Slack", "pid": 67890, "download": 567890, "upload": 12345}
}
```

### 核心逻辑

在 `ProcessReader` 类中新增：

1. **当前小时缓存**：内存中维护当前小时的数据桶
2. **小时切换检测**：检测小时变化时，将缓存持久化到数据库
3. **流量累加**：每次读取时，将进程流量累加到对应的桶中

### 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `Modules/Net/readers.swift` | 在 `ProcessReader` 中新增存储逻辑和 `terminate()` 方法 |
| `Modules/Net/main.swift` | 在模块终止时调用 `processReader?.terminate()` |

### 代码变更概要

```swift
// ProcessReader 类新增属性
private var _currentHourBucket: ProcessTrafficBucket = [:]
private var _currentHourKey: String = ""
private let trafficQueue = DispatchQueue(label: "eu.exelban.ProcessTrafficQueue")
private let trafficDBKey = "process_traffic"

private var currentHourBucket: ProcessTrafficBucket {
    get { self.trafficQueue.sync { self._currentHourBucket } }
    set { self.trafficQueue.sync { self._currentHourBucket = newValue } }
}

private var currentHourKey: String {
    get { self.trafficQueue.sync { self._currentHourKey } }
    set { self.trafficQueue.sync { self._currentHourKey = newValue } }
}

// 在 read() 方法末尾新增
private func recordTraffic(_ processes: [Network_Process]) {
    let now = Date()
    let hourKey = self.getHourKey(now)

    // 检测小时切换（支持跨多小时的情况）
    if self.currentHourKey != hourKey {
        if !self.currentHourKey.isEmpty {
            self.saveBucket(self.currentHourKey, self.currentHourBucket)
        }
        self.currentHourKey = hourKey
        self.currentHourBucket = [:]
    }

    // 累加流量（使用 pid + name 组合避免重名问题）
    for process in processes {
        let uniqueKey = "\(process.name)_\(process.pid)"
        if self.currentHourBucket[uniqueKey] == nil {
            self.currentHourBucket[uniqueKey] = ProcessTrafficRecord(
                name: process.name,
                pid: process.pid
            )
        }
        self.currentHourBucket[uniqueKey]?.download += Int64(process.download)
        self.currentHourBucket[uniqueKey]?.upload += Int64(process.upload)
    }
}

private func getHourKey(_ date: Date) -> String {
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy-MM-dd|HH"
    return "\(self.trafficDBKey)|\(formatter.string(from: date))"
}

private func saveBucket(_ key: String, _ bucket: ProcessTrafficBucket) {
    guard !bucket.isEmpty else { return }
    do {
        let data = try JSONEncoder().encode(bucket)
        guard let json = String(data: data, encoding: .utf8) else { return }
        let success = DB.shared.lldb?.insert(key, value: json) ?? false
        if !success {
            debug("Failed to save process traffic bucket: \(key)")
        }
    } catch {
        debug("Failed to encode process traffic bucket: \(error)")
    }
}

// 应用终止时保存当前数据
func terminate() {
    if !self.currentHourKey.isEmpty && !self.currentHourBucket.isEmpty {
        self.saveBucket(self.currentHourKey, self.currentHourBucket)
    }
}
```

### 数据保留策略

- **永不自动清理**（用户选择）
- 数据库位于：`~/Library/Application Support/Stats/lldb/`
- 用户可手动删除数据库文件来清理

## 外部工具支持

### 数据读取方式

LevelDB 数据可使用多种语言读取：

**Python 示例**：
```python
import plyvel  # pip install plyvel

db = plyvel.DB('/Users/xxx/Library/Application Support/Stats/lldb')
for key, value in db.iterator(prefix=b'process_traffic|'):
    print(key.decode(), value.decode())
```

**导出脚本**（可后续提供）：
- 将指定日期范围的数据导出为 JSON 文件
- 生成简单的 HTML 报告

## 测试计划

1. **单元测试**：验证小时 key 生成、流量累加逻辑
2. **集成测试**：验证数据正确存储到 LevelDB
3. **手动测试**：运行应用一段时间后，检查数据库中是否有正确的数据

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 数据库写入频繁影响性能 | 使用内存缓存，每小时才写入一次 |
| 进程名重复（如同名应用） | 使用 `{name}_{pid}` 组合作为 key |
| 数据库损坏 | LevelDB 有较好的容错机制；用户可删除重建 |
| 应用异常退出数据丢失 | 添加 `terminate()` 方法保存当前缓存 |
| 线程安全问题 | 使用 `DispatchQueue` 保护共享状态 |
| 应用休眠后错过小时切换 | 下次读取时检测并保存（数据归属上一个小时） |

## 时间线

- 阶段 1：修改 `readers.swift`，实现存储逻辑
- 阶段 2：编写数据导出脚本（可选）
- 阶段 3：测试验证

## 附录：数据库位置

```
~/Library/Application Support/Stats/lldb/
```

如需查看数据，可使用 LevelDB 浏览工具或我提供的导出脚本。
