#!/usr/bin/env python3
import os
import json
import logging
from typing import Dict, Any

def get_log_level():
    level = os.environ.get("LOG_LEVEL", "DEBUG").upper()
    return getattr(logging, level, logging.WARNING)

logging.basicConfig(
    level=get_log_level(),
    format='%(asctime)s %(levelname)s %(message)s'
)

def find_latest_files(root_dir: str) -> Dict[str, str]:
    """
    Recursively find all files under root_dir, keeping only the latest file for each filename.
    Returns a dict: {filename: full_path_to_latest_file}
    """
    latest_files = {}
    for dirpath, _, filenames in os.walk(root_dir):
        logging.debug(f"Searching in directory: {dirpath}")
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            logging.debug(f"Found file: {fpath}")
            if fname not in latest_files:
                latest_files[fname] = fpath
                logging.info(f"Adding new file: {fname} -> {fpath}")
            else:
                if os.path.getmtime(fpath) > os.path.getmtime(latest_files[fname]):
                    logging.info(f"Replacing older file for {fname}: {latest_files[fname]} with {fpath}")
                    latest_files[fname] = fpath
    logging.debug(f"Latest files: {latest_files}")
    return latest_files

def extract_tasks_with_worklog(files: Dict[str, str], email: str) -> Dict[str, Any]:
    """
    For each file, check if it contains a worklog entry with the given email (nested Jira structure).
    If so, extract task key, summary, and description.
    Returns a dict: {task_key: {summary: ..., description: ...}}
    """
    result = {}
    for fpath in files.values():
        try:
            logging.debug(f"Processing file: {fpath}")
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Jira-like structure: key at root, summary/description/worklog under fields
            key = data.get("key")
            fields = data.get("fields", {})
            summary = fields.get("summary")
            description = fields.get("description")
            worklog = fields.get("worklog", {})
            worklogs = worklog.get("worklogs", [])
            if not (key and summary and description and isinstance(worklogs, list)):
                logging.warning(f"File {fpath} missing required fields, skipping.")
                continue
            found = False
            for wl in worklogs:
                author = wl.get("author", {})
                wl_email = author.get("emailAddress")
                if wl_email == email:
                    found = True
                    break
            if found:
                logging.info(f"Match found in {fpath} for email {email}")
                result[key] = {
                    "summary": summary,
                    "description": description
                }
            else:
                logging.debug(f"No matching worklog for email {email} in {fpath}")
        except Exception as e:
            logging.error(f"Error processing file {fpath}: {e}")
            continue
    logging.debug(f"Result: {result}")
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Find tasks with worklog by email.")
    parser.add_argument("root_dir", help="Root directory to search")
    parser.add_argument("email", help="Email address to search for in worklogs")
    parser.add_argument("--output", default="result.json", help="Output JSON file")
    args = parser.parse_args()

    logging.info(f"Starting search in {args.root_dir} for worklogs by {args.email}")
    latest_files = find_latest_files(args.root_dir)
    result = extract_tasks_with_worklog(latest_files, args.email)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logging.info(f"Result saved to {args.output}")

if __name__ == "__main__":
    main()
