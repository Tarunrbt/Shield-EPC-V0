#!/usr/bin/env python3
"""
Repository Audit Script (Read-Only)
------------------------------------
Scans a repository directory tree and reports:
  - Empty folders
  - Duplicate files (by SHA-256 hash)
  - Large files (> 10 MB)

This script performs NO file modifications, moves, or deletions.
It only reads file metadata/content to compute hashes and sizes.

Usage:
    python repo_audit.py /path/to/repo [--output report.txt]
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict
from datetime import datetime

# Directories to skip during the walk
IGNORED_DIRS = {"__pycache__", ".git", ".pytest_cache", "node_modules"}

# Threshold for "large file" classification (10 MB)
LARGE_FILE_THRESHOLD_BYTES = 10 * 1024 * 1024

# Chunk size for streaming hash computation (avoids loading huge files into memory)
HASH_CHUNK_SIZE = 65536  # 64 KB


def sha256_of_file(filepath):
    """Compute the SHA-256 hash of a file's contents, reading in chunks."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(HASH_CHUNK_SIZE), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError) as e:
        print(f"  [WARN] Could not read '{filepath}': {e}", file=sys.stderr)
        return None


def human_readable_size(num_bytes):
    """Convert a byte count into a human-readable string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def audit_repository(root_path):
    """
    Walk the repository tree and gather audit data.

    Returns a dict with:
        empty_folders: list of paths
        duplicates: dict of hash -> list of file paths (only entries with >1 file)
        large_files: list of (path, size_in_bytes)
        stats: summary counters
    """
    empty_folders = []
    hash_to_files = defaultdict(list)
    large_files = []

    total_files_scanned = 0
    total_dirs_scanned = 0
    unreadable_files = 0

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # Prune ignored directories in-place so os.walk() doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        total_dirs_scanned += 1

        # Empty folder check: no subdirectories and no files
        if not dirnames and not filenames:
            empty_folders.append(dirpath)

        for filename in filenames:
            filepath = os.path.join(dirpath, filename)

            # Skip broken symlinks / inaccessible entries gracefully
            if not os.path.isfile(filepath) or os.path.islink(filepath) and not os.path.exists(filepath):
                continue

            try:
                file_size = os.path.getsize(filepath)
            except OSError as e:
                print(f"  [WARN] Could not stat '{filepath}': {e}", file=sys.stderr)
                unreadable_files += 1
                continue

            total_files_scanned += 1

            # Large file check
            if file_size > LARGE_FILE_THRESHOLD_BYTES:
                large_files.append((filepath, file_size))

            # Duplicate detection via SHA-256
            file_hash = sha256_of_file(filepath)
            if file_hash is None:
                unreadable_files += 1
                continue

            hash_to_files[file_hash].append(filepath)

    # Keep only hashes that have more than one associated file (true duplicates)
    duplicates = {h: paths for h, paths in hash_to_files.items() if len(paths) > 1}

    stats = {
        "total_dirs_scanned": total_dirs_scanned,
        "total_files_scanned": total_files_scanned,
        "unreadable_files": unreadable_files,
        "empty_folder_count": len(empty_folders),
        "duplicate_group_count": len(duplicates),
        "duplicate_file_count": sum(len(v) for v in duplicates.values()),
        "large_file_count": len(large_files),
    }

    return {
        "empty_folders": empty_folders,
        "duplicates": duplicates,
        "large_files": large_files,
        "stats": stats,
    }


def build_report(root_path, results):
    """Build a formatted text report from audit results as a list of lines."""
    lines = []
    stats = results["stats"]

    lines.append("=" * 70)
    lines.append("REPOSITORY AUDIT REPORT")
    lines.append("=" * 70)
    lines.append(f"Root path:      {os.path.abspath(root_path)}")
    lines.append(f"Generated at:   {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Ignored dirs:   {', '.join(sorted(IGNORED_DIRS))}")
    lines.append(f"Mode:           READ-ONLY (no files modified or deleted)")
    lines.append("")

    lines.append("-" * 70)
    lines.append("SUMMARY")
    lines.append("-" * 70)
    lines.append(f"Directories scanned:     {stats['total_dirs_scanned']}")
    lines.append(f"Files scanned:           {stats['total_files_scanned']}")
    lines.append(f"Unreadable files:        {stats['unreadable_files']}")
    lines.append(f"Empty folders found:     {stats['empty_folder_count']}")
    lines.append(f"Duplicate groups found:  {stats['duplicate_group_count']}")
    lines.append(f"  (total files involved: {stats['duplicate_file_count']})")
    lines.append(f"Large files (>10 MB):    {stats['large_file_count']}")
    lines.append("")

    # --- Empty folders ---
    lines.append("-" * 70)
    lines.append(f"EMPTY FOLDERS ({len(results['empty_folders'])})")
    lines.append("-" * 70)
    if results["empty_folders"]:
        for folder in sorted(results["empty_folders"]):
            lines.append(f"  {folder}")
    else:
        lines.append("  None found.")
    lines.append("")

    # --- Duplicate files ---
    lines.append("-" * 70)
    lines.append(f"DUPLICATE FILES ({len(results['duplicates'])} groups)")
    lines.append("-" * 70)
    if results["duplicates"]:
        for i, (file_hash, paths) in enumerate(
            sorted(results["duplicates"].items(), key=lambda kv: -len(kv[1])), start=1
        ):
            lines.append(f"  Group {i}  |  SHA-256: {file_hash}  |  {len(paths)} copies")
            for p in sorted(paths):
                try:
                    size = human_readable_size(os.path.getsize(p))
                except OSError:
                    size = "unknown size"
                lines.append(f"      - {p} ({size})")
            lines.append("")
    else:
        lines.append("  None found.")
        lines.append("")

    # --- Large files ---
    lines.append("-" * 70)
    lines.append(f"LARGE FILES > 10 MB ({len(results['large_files'])})")
    lines.append("-" * 70)
    if results["large_files"]:
        for path, size in sorted(results["large_files"], key=lambda x: -x[1]):
            lines.append(f"  {human_readable_size(size):>12}   {path}")
    else:
        lines.append("  None found.")
    lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    lines.append("=" * 70)

    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Read-only repository audit: finds empty folders, duplicate "
                     "files (via SHA-256), and files larger than 10 MB."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root path of the repository to audit (default: current directory)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Optional path to write the report to a text file (in addition to printing it)",
    )
    args = parser.parse_args()

    root_path = args.path

    if not os.path.isdir(root_path):
        print(f"Error: '{root_path}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning '{os.path.abspath(root_path)}' (read-only)...\n")

    results = audit_repository(root_path)
    report_lines = build_report(root_path, results)
    report_text = "\n".join(report_lines)

    print(report_text)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report_text + "\n")
            print(f"\nReport written to: {os.path.abspath(args.output)}")
        except OSError as e:
            print(f"\n[WARN] Could not write report file: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
