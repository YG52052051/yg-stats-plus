import Cocoa

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var serverProcess: Process?
    let port = 8765

    var dataDir: String {
        return NSHomeDirectory() + "/Library/Application Support/Stats"
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupStatusBar()
        setupAndStartServer()
    }

    // MARK: - Status Bar

    func setupStatusBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        updateIcon(running: false)

        let menu = NSMenu()
        menu.addItem(withTitle: "打开流量查看器", action: #selector(openViewer(_:)), keyEquivalent: "o")
        menu.addItem(NSMenuItem.separator())
        menu.addItem(withTitle: "重启服务", action: #selector(restartServer(_:)), keyEquivalent: "r")
        menu.addItem(NSMenuItem.separator())
        let authorItem = NSMenuItem(title: "作者：宇哥52052051", action: nil, keyEquivalent: "")
        authorItem.isEnabled = false
        menu.addItem(authorItem)
        menu.addItem(NSMenuItem.separator())
        menu.addItem(withTitle: "退出", action: #selector(quitApp(_:)), keyEquivalent: "q")
        statusItem.menu = menu
    }

    func updateIcon(running: Bool) {
        DispatchQueue.main.async { [weak self] in
            guard let self = self, let button = self.statusItem.button else { return }
            let symbol = running ? "network" : "exclamationmark.triangle"
            if let image = NSImage(systemSymbolName: symbol, accessibilityDescription: "Traffic Viewer") {
                image.size = NSSize(width: 18, height: 18)
                button.image = image
            }
            button.toolTip = running
                ? "Traffic Viewer 运行中 (端口 \(self.port))"
                : "Traffic Viewer 服务未运行"
        }
    }

    // MARK: - Server Management

    func setupAndStartServer() {
        // 确保数据目录存在
        try? FileManager.default.createDirectory(
            atPath: dataDir, withIntermediateDirectories: true
        )

        // 从 .app 包内复制 HTML 到数据目录
        if let htmlURL = Bundle.main.url(forResource: "traffic_viewer", withExtension: "html") {
            let destURL = URL(fileURLWithPath: dataDir)
                .appendingPathComponent("traffic_viewer.html")
            try? FileManager.default.removeItem(at: destURL)
            try? FileManager.default.copyItem(at: htmlURL, to: destURL)
        }

        startServer()
    }

    func startServer() {
        // 停止已有进程
        if let process = serverProcess, process.isRunning {
            process.terminate()
            process.waitUntilExit()
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = ["-c", "cd '\(dataDir)' && exec python3 -m http.server \(port)"]

        // 设置环境变量，确保能找到 python3
        var env = ProcessInfo.processInfo.environment
        let userPath = env["PATH"] ?? ""
        env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + userPath
        process.environment = env

        // 静默输出
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe

        // 进程退出时更新图标
        process.terminationHandler = { [weak self] _ in
            self?.updateIcon(running: false)
        }

        do {
            try process.run()
            serverProcess = process
            updateIcon(running: true)
        } catch {
            print("启动服务器失败: \(error)")
            updateIcon(running: false)
        }
    }

    // MARK: - Menu Actions

    @objc func openViewer(_ sender: Any?) {
        if let url = URL(string: "http://localhost:\(port)/traffic_viewer.html") {
            NSWorkspace.shared.open(url)
        }
    }

    @objc func restartServer(_ sender: Any?) {
        setupAndStartServer()
    }

    @objc func quitApp(_ sender: Any?) {
        serverProcess?.terminate()
        NSApplication.shared.terminate(nil)
    }
}

// 启动应用（菜单栏模式，不显示 Dock 图标）
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.accessory)
app.run()
