#!/usr/bin/env python3
"""把旧单文件流量历史合并进月份分片。

背景：旧版 ProcessReader 每 5 分钟全量重写 traffic_history.json（含全部历史），
因此该文件始终是最完整的权威快照。新版改为按月分片（traffic_history_YYYY-MM.json，
写入端只重写当月）。本脚本用于新旧切换期：以旧单文件为源，与现有分片做合并。

合并规则（槽级，幂等，可重复执行）：
- 槽在分片中已存在 → 保留分片版本（分片由最近一次写入者拥有；新旧版本切换时
  跨界槽以分片即新版数据为准），旧单文件同槽中分片缺少的进程键补入
- 槽只在旧单文件存在 → 整槽取旧单文件（补历史缺口）

典型用法（装新版前后各跑一次）：
    python3 tools/migrate_traffic_shards.py          # 干跑，只显示统计
    python3 tools/migrate_traffic_shards.py --apply  # 实际写盘
"""

import argparse
import json
import os
import sys
import tempfile

DATA_DIR = os.path.expanduser("~/Library/Application Support/Stats")
SINGLE_FILE = os.path.join(DATA_DIR, "traffic_history.json")
MANIFEST_FILE = os.path.join(DATA_DIR, "traffic_months.json")
SHARD_PREFIX = "traffic_history_"
SHARD_SUFFIX = ".json"


def shard_name(month: str) -> str:
    return f"{SHARD_PREFIX}{month}{SHARD_SUFFIX}"


def atomic_write_json(path: str, obj) -> None:
    """tmp 文件 + 原子替换，避免写一半崩溃损坏 JSON。"""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def load_json(path: str):
    with open(path) as f:
        return json.load(f)


def count_slots(month_data: dict) -> int:
    return sum(len(slots) for slots in month_data.values())


def group_by_month(single_data: dict) -> dict:
    """把 {date: {slot: {procKey: record}}} 按月份分组。"""
    months: dict = {}
    for date, slots in single_data.items():
        month = date[:7]  # YYYY-MM-DD -> YYYY-MM
        months.setdefault(month, {})[date] = slots
    return months


def merge_month(shard_data: dict, single_month: dict) -> tuple:
    """单文件某月数据合并进该月分片，返回 (合并结果, 新增槽数)。"""
    merged = json.loads(json.dumps(shard_data)) if shard_data else {}
    added_slots = 0
    for date, slots in single_month.items():
        for slot, procs in slots.items():
            existing_slot = merged.get(date, {}).get(slot)
            if existing_slot is None:
                merged.setdefault(date, {})[slot] = procs
                added_slots += 1
            else:
                # 槽已存在（分片更新）：只补分片缺少的进程键
                for key, record in procs.items():
                    if key not in existing_slot:
                        existing_slot[key] = record
    return merged, added_slots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="实际写盘（默认干跑）")
    args = parser.parse_args()

    if not os.path.exists(SINGLE_FILE):
        print(f"旧单文件不存在: {SINGLE_FILE}")
        return 1

    print(f"读取旧单文件: {SINGLE_FILE}")
    single_data = load_json(SINGLE_FILE)
    single_months = group_by_month(single_data)
    print(f"共 {len(single_data)} 天 / {len(single_months)} 个月: "
          f"{min(single_months)} ~ {max(single_months)}")

    total_added = 0
    changed_months = 0
    for month in sorted(single_months):
        shard_path = os.path.join(DATA_DIR, shard_name(month))
        shard_data = load_json(shard_path) if os.path.exists(shard_path) else {}
        merged, added = merge_month(shard_data, single_months[month])
        changed = added > 0 or merged != shard_data
        if changed:
            changed_months += 1
        action = "WRITE" if (changed and args.apply) else ("change" if changed else "ok")
        print(f"  {month}: 分片 {count_slots(shard_data)} 槽 -> {count_slots(merged)} 槽, "
              f"补入 {added} 槽 [{action}]")
        total_added += added
        if changed and args.apply:
            atomic_write_json(shard_path, merged)

    if args.apply:
        # 维护月份清单（与写入端一致：目录扫描，内容有变化才重写）
        month_files = sorted(
            f for f in os.listdir(DATA_DIR)
            if f.startswith(SHARD_PREFIX) and f.endswith(SHARD_SUFFIX)
        )
        manifest_new = json.dumps(month_files, indent=2)
        manifest_old = None
        if os.path.exists(MANIFEST_FILE):
            with open(MANIFEST_FILE) as f:
                manifest_old = f.read()
        if manifest_new != manifest_old:
            with open(MANIFEST_FILE, "w") as f:
                f.write(manifest_new + "\n")
            print(f"清单已更新: {MANIFEST_FILE} ({len(month_files)} 个月份)")
        else:
            print(f"清单无变化: {MANIFEST_FILE}")
        print(f"完成: {changed_months} 个分片有变化, 共补入 {total_added} 槽")
    else:
        print(f"[干跑] {changed_months} 个月份有变化, 共需补入 {total_added} 槽; 加 --apply 实际写盘")

    return 0


if __name__ == "__main__":
    sys.exit(main())
