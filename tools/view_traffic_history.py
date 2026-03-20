#!/usr/bin/env python3
"""
Stats - Process Traffic History Viewer

This script reads and displays process traffic history data from the Stats LevelDB database.

Usage:
    python3 view_traffic_history.py                    # Show today's data
    python3 view_traffic_history.py --date 2026-03-19   # Show specific date
    python3 view_traffic_history.py --range 7           # Show last 7 days
    python3 view_traffic_history.py --export output.json  # Export to JSON

Requirements:
    pip install plyvel
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import plyvel
except ImportError:
    print("Error: plyvel is required. Install with: pip install plyvel")
    sys.exit(1)


def get_db_path():
    """Get the LevelDB database path."""
    home = Path.home()
    db_path = home / "Library" / "Application Support" / "Stats" / "lldb"
    if db_path.exists():
        return str(db_path)
    return None


def read_traffic_data(db, date_str=None, days=1):
    """Read traffic data from LevelDB."""
    prefix = b"process_traffic|"

    results = []

    for key, value in db.iterator(prefix=prefix):
        try:
            key_str = key.decode('utf-8')
            value_str = value.decode('utf-8')
            data = json.loads(value_str)

            # Parse date from key: process_traffic|YYYY-MM-DD|HH
            parts = key_str.split("|")
            if len(parts) >= 3:
                record_date = parts[1]
                record_hour = parts[2]
            else:
                continue

            # Filter by date if specified
            if date_str and record_date != date_str:
                continue

            results.append({
                "key": key_str,
                "date": record_date,
                "hour": record_hour,
                "data": data
            })
        except Exception as e:
            continue

    return results


def aggregate_by_process(records):
    """Aggregate traffic data by process name."""
    process_totals = {}

    for record in records:
        for process_key, traffic in record["data"].items():
            name = traffic.get("name", process_key)
            if name not in process_totals:
                process_totals[name] = {
                    "download": 0,
                    "upload": 0,
                    "hours": set()
                }
            process_totals[name]["download"] += traffic.get("download", 0)
            process_totals[name]["upload"] += traffic.get("upload", 0)
            process_totals[name]["hours"].add(record["hour"])

    # Convert sets to sorted lists
    for name in process_totals:
        process_totals[name]["hours"] = sorted(process_totals[name]["hours"])

    return process_totals


def format_bytes(bytes_val):
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(bytes_val) < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def print_report(records, process_totals, date_filter=None):
    """Print a formatted report."""
    print("\n" + "="*70)
    print("  Stats - Process Traffic History Report")
    print("="*70)

    if date_filter:
        print(f"\nDate: {date_filter}")
    else:
        dates = sorted(set(r["date"] for r in records))
        if dates:
            print(f"\nDate range: {dates[0]} to {dates[-1]}")

    print(f"Total records: {len(records)}")
    print(f"Total processes: {len(process_totals)}")

    print("\n" + "-"*70)
    print("  Top Processes by Total Traffic")
    print("-"*70)
    print(f"{'Process':<30} {'Download':>15} {'Upload':>15} {'Total':>15}")
    print("-"*70)

    # Sort by total traffic
    sorted_processes = sorted(
        process_totals.items(),
        key=lambda x: x[1]["download"] + x[1]["upload"],
        reverse=True
    )

    for name, data in sorted_processes[:20]:  # Top 20
        download = data["download"]
        upload = data["upload"]
        total = download + upload
        print(f"{name[:28]:<30} {format_bytes(download):>15} {format_bytes(upload):>15} {format_bytes(total):>15}")

    print("\n" + "-"*70)
    print(f"  {'TOTAL':<30} ", end="")
    total_download = sum(d["download"] for d in process_totals.values())
    total_upload = sum(d["upload"] for d in process_totals.values())
    print(f"{format_bytes(total_download):>15} {format_bytes(total_upload):>15} {format_bytes(total_download + total_upload):>15}")
    print()


def export_json(records, process_totals, output_file):
    """Export data to JSON file."""
    export_data = {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(records),
        "records": records,
        "process_totals": {
            name: {
                **data,
                "download_formatted": format_bytes(data["download"]),
                "upload_formatted": format_bytes(data["upload"])
            }
            for name, data in process_totals.items()
        }
    }

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"Data exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='View Stats process traffic history')
    parser.add_argument('--date', type=str, help='Specific date (YYYY-MM-DD)')
    parser.add_argument('--range', type=int, default=1, help='Number of days to show (default: 1)')
    parser.add_argument('--export', type=str, help='Export to JSON file')
    parser.add_argument('--db-path', type=str, help='Custom database path')
    args = parser.parse_args()

    # Get database path
    db_path = args.db_path or get_db_path()
    if not db_path:
        print("Error: Could not find Stats database.")
        print("Make sure Stats app is installed and has been run at least once.")
        print("\nCustom path can be specified with --db-path")
        sys.exit(1)

    print(f"Database: {db_path}")

    try:
        db = plyvel.DB(db_path)
    except Exception as e:
        print(f"Error opening database: {e}")
        sys.exit(1)

    try:
        # Read data
        records = read_traffic_data(db, args.date, args.range)

        if not records:
            print("No traffic data found.")
            if args.date:
                print(f"No data for date: {args.date}")
            else:
                print("Try running the Stats app for a while first.")
            return

        # Aggregate by process
        process_totals = aggregate_by_process(records)

        # Print report
        print_report(records, process_totals, args.date)

        # Export if requested
        if args.export:
            export_json(records, process_totals, args.export)

    finally:
        db.close()


if __name__ == "__main__":
    main()
