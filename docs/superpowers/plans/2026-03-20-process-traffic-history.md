# 进程流量历史记录功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 ProcessReader 中添加流量历史记录功能，将进程级网络流量按小时存储到 LevelDB

**Architecture:** 复用现有 DB.shared (LevelDB)，在 ProcessReader.read() 末尾新增流量累加逻辑，按小时分桶存储 JSON 数据

**Tech Stack:** Swift, LevelDB (现有 LLDB wrapper), JSONEncoder

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `Modules/Net/readers.swift` | 修改 | 添加数据结构、存储逻辑、terminate 方法 |
| `Modules/Net/main.swift` | 修改 | 添加 deinit 调用 processReader.terminate() |

---

## Task 1: 添加数据结构定义

**Files:**
- Modify: `Modules/Net/readers.swift:550` (ProcessReader 类定义之前)

- [ ] **Step 1: 在 ProcessReader 类之前添加数据结构**

在 `readers.swift` 文件中，找到 `public class ProcessReader` 这一行（约第552行），在其**之前**添加：

```swift
// MARK: - Process Traffic History

struct ProcessTrafficRecord: Codable {
    let name: String
    let pid: Int
    var download: Int64 = 0
    var upload: Int64 = 0
}

typealias ProcessTrafficBucket = [String: ProcessTrafficRecord]
```

- [ ] **Step 2: 验证代码位置正确**

确认新代码在 `ProcessReader` 类定义之前，`UsageReader` 类定义之后（约第550行附近）。

---

## Task 2: 在 ProcessReader 中添加存储相关属性

**Files:**
- Modify: `Modules/Net/readers.swift:552-560` (ProcessReader 类属性区域)

- [ ] **Step 1: 在 ProcessReader 类中添加新属性**

在 `ProcessReader` 类的 `private var previous` 属性之后添加：

```swift
// Traffic history storage
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
```

---

## Task 3: 添加辅助方法

**Files:**
- Modify: `Modules/Net/readers.swift:688` (ProcessReader 类末尾，read() 方法之后)

- [ ] **Step 1: 在 read() 方法末尾之后、类结束括号之前添加方法**

在 `self.callback(processes.suffix(self.numberOfProcesses).reversed())` 这行之后，类结束的 `}` 之前添加：

```swift
// MARK: - Traffic History

private func recordTraffic(_ processes: [Network_Process]) {
    let now = Date()
    let hourKey = self.getHourKey(now)

    // 检测小时切换
    if self.currentHourKey != hourKey {
        if !self.currentHourKey.isEmpty {
            self.saveBucket(self.currentHourKey, self.currentHourBucket)
        }
        self.currentHourKey = hourKey
        self.currentHourBucket = [:]
    }

    // 累加流量
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

public override func terminate() {
    if !self.currentHourKey.isEmpty && !self.currentHourBucket.isEmpty {
        self.saveBucket(self.currentHourKey, self.currentHourBucket)
    }
}
```

---

## Task 4: 在 read() 方法中调用 recordTraffic

**Files:**
- Modify: `Modules/Net/readers.swift:687` (read() 方法末尾)

- [ ] **Step 1: 在 read() 方法最后一行 callback 调用之后添加**

找到：
```swift
self.callback(processes.suffix(self.numberOfProcesses).reversed())
```

在其之后添加：
```swift
self.recordTraffic(Array(processes.suffix(self.numberOfProcesses).reversed()))
```

---

## Task 5: 添加 terminate 生命周期调用

**Files:**
- Modify: `Modules/Net/main.swift:137` (Network 类定义区域)

- [ ] **Step 1: 在 Network 类中添加 deinit 方法**

在 `Network` 类中（约第137行 `public class Network: Module` 之后），找到合适位置添加：

```swift
deinit {
    self.processReader?.terminate()
}
```

最佳位置：在 `public init()` 方法之后（约第228行附近）。

---

## Task 6: 手动测试验证

由于项目没有自动化测试，需要手动验证：

- [ ] **Step 1: 确认代码编译通过**

在 Xcode 中 Build 项目 (Cmd+B)，确认没有编译错误。

- [ ] **Step 2: 运行应用 1-2 分钟**

运行 Stats 应用，正常使用网络。

- [ ] **Step 3: 检查数据库中是否有数据**

```bash
# 查看数据库文件
ls ~/Library/Application\ Support/Stats/lldb/

# 使用 Python 读取数据（需要安装 plyvel）
python3 -c "
import plyvel
db = plyvel.DB('/Users/$(whoami)/Library/Application Support/Stats/lldb')
for k, v in db.iterator(prefix=b'process_traffic|'):
    print(k.decode(), v.decode()[:100])
"
```

- [ ] **Step 4: 提交代码**

```bash
git add Modules/Net/readers.swift
git commit -m "feat(network): add process traffic history recording

- Add ProcessTrafficRecord struct for storing per-process traffic data
- Record traffic data hourly to LevelDB
- Support app termination with data persistence"
```

---

## 数据格式参考

存储在 LevelDB 中的数据格式：

**Key:** `process_traffic|2026-03-20|14`

**Value (JSON):**
```json
{
  "Safari_12345": {"name": "Safari", "pid": 12345, "download": 1234567, "upload": 234567},
  "Slack_67890": {"name": "Slack", "pid": 67890, "download": 567890, "upload": 12345}
}
```

---

## 后续（可选）

如果需要查看数据的工具，可以另外创建：
- Python 脚本导出 JSON
- HTML 查看器
