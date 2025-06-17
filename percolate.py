#!/usr/bin/env python3
import os
import json
from typing import Dict, Any

def find_latest_files(root_dir: str) -> Dict[str, str]:
    """
    Recursively find all files under root_dir, keeping only the latest file for each filename.
    Returns a dict: {filename: full_path_to_latest_file}
    """
    latest_files = {}
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            if fname not in latest_files:
                latest_files[fname] = fpath
            else:
                if os.path.getmtime(fpath) > os.path.getmtime(latest_files[fname]):
                    latest_files[fname] = fpath
    return latest_files

def extract_tasks_with_worklog(files: Dict[str, str], email: str) -> Dict[str, Any]:
    """
    For each file, check if it contains a worklog entry with the given email.
    If so, extract task key, summary, and description.
    Returns a dict: {task_key: {summary: ..., description: ...}}
    """
    result = {}
    for fpath in files.values():
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Assume file is a dict with keys: key, summary, description, worklog
            if not all(k in data for k in ("key", "summary", "description", "worklog")):
                continue
            if any(wl.get("email") == email for wl in data["worklog"]):
                result[data["key"]] = {
                    "summary": data["summary"],
                    "description": data["description"]
                }
        except Exception:
            continue  # skip files that can't be parsed
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find tasks with worklog by email.")
    parser.add_argument("root_dir", help="Root directory to search")
    parser.add_argument("email", help="Email address to search for in worklogs")
    parser.add_argument("--output", default="result.json", help="Output JSON file")
    args = parser.parse_args()

    latest_files = find_latest_files(args.root_dir)
    result = extract_tasks_with_worklog(latest_files, args.email)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Result saved to {args.output}")

if __name__ == "__main__":
    main()
