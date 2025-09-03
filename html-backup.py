#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys

PATH_SETS = {
    "branch-01": [
        "/phone",
        "/phone/specs",
        "/phone/compare",
    ],
    "branch-02": [
        "/watch",
        "/watch/compare",
        "/watch/feature-availity",
    ],
    "branch-03": [
        "/os",
        "/os/ios",
        "/os/macos",
        "/os/watchos",
    ],
}

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"

BACKUP_PREFIX = "__index"
BACKUP_GLOB = "__index*.bak.html"

def normalize_rel(s: str) -> Path:
    return Path(s.lstrip("/"))

def collect_paths(set_name: str | None):
    if set_name is None or str(set_name).lower() in ("all", "-a", "--all"):
        seen, out = set(), []
        for paths in PATH_SETS.values():
            for p in paths:
                if p not in seen:
                    seen.add(p)
                    out.append(p)
        return out
    if set_name not in PATH_SETS:
        print(f"[error] unknown set: {set_name}. Try 'html-backup help'.")
        sys.exit(1)
    return PATH_SETS[set_name]

def _run_svn_info_show_item(item: str, path: Path, rev: str | None = None):
    cmd = ["svn", "info", "--show-item", item]

    if rev:
        cmd += ["-r", rev]
    cmd.append(str(path))
    try:
        res = subprocess.run(
            cmd, check=False, capture_output=True, text=True, cwd=str(path.parent)
        )
    except FileNotFoundError:
        return False, None, "svn not found in PATH"

    if res.returncode != 0:
        msg = res.stderr.strip() or res.stdout.strip() or "svn info failed"
        return False, None, msg

    try:
        val = int(res.stdout.strip())
        return True, val, ""
    except ValueError:
        return False, None, f"could not parse svn info output: {res.stdout!r}"

def svn_working_revision(path: Path):
    return _run_svn_info_show_item("revision", path)

def svn_last_changed_revision(path: Path, rev: str | None = None):
    return _run_svn_info_show_item("last-changed-revision", path, rev=rev)

def backup_one(base: Path, rel_folder: Path):
    folder = base / rel_folder
    if not folder.is_dir():
        return ("fail", str(rel_folder), "folder is missing")

    src = folder / "index.html"
    if not src.is_file():
        return ("fail", str(rel_folder), "index.html is missing")

    ok_rev, wc_rev, _ = svn_working_revision(src)
    rev_str = f"{wc_rev:06d}" if ok_rev and isinstance(wc_rev, int) else "000000"

    ts = datetime.now().strftime("%y%m%d-%H%M")
    dst_name = f"{BACKUP_PREFIX}_{ts}_r{rev_str}.bak.html"
    dst = folder / dst_name

    try:
        shutil.copy2(src, dst)
    except Exception as e:
        return ("fail", str(rel_folder), f"copy failed: {e}")

    return ("ok", str(rel_folder), f"created {dst.name}")

def delete_in_folder(base: Path, rel_folder: Path):
    folder = base / rel_folder
    if not folder.is_dir():
        return ("fail", str(rel_folder), "folder is missing")

    deleted, errors = [], []
    for p in folder.glob(BACKUP_GLOB):
        try:
            p.unlink()
            deleted.append(p.name)
        except Exception as e:
            errors.append((str(rel_folder), f"delete failed for {p.name}: {e}"))

    if errors:
        first = errors[0]
        return ("fail", first[0], first[1])

    if deleted:
        msg = f"deleted {len(deleted)} file(s): {', '.join(deleted)}"
        return ("ok", str(rel_folder), msg)

    return ("fail", str(rel_folder), "no backup files found")

def check_update_one(base: Path, rel_folder: Path):
    folder = base / rel_folder
    if not folder.is_dir():
        return ("fail", str(rel_folder), "folder is missing")

    target = folder / "index.html"
    if not target.is_file():
        return ("fail", str(rel_folder), "index.html is missing")

    ok_local, local_changed, err_local = svn_last_changed_revision(target)
    if not ok_local:
        return ("fail", str(rel_folder), err_local)

    ok_latest, latest_changed, err_latest = svn_last_changed_revision(target, rev="HEAD")
    if not ok_latest:
        return ("fail", str(rel_folder), err_latest)

    if latest_changed > local_changed:
        return ("ok", str(rel_folder),
                f"update available for index.html (local {local_changed} -> latest {latest_changed})")
    else:
        return ("ok", str(rel_folder), "up-to-date")

def show_help():
    print("Usage:")
    print("  html-backup                 # backup all sets")
    print("  html-backup <set>           # backup a specific set")
    print("  html-backup delete          # delete backups in all sets")
    print("  html-backup delete <set>    # delete backups in a specific set")
    print("  html-backup check           # check updates for all sets")
    print("  html-backup check <set>     # check updates for a specific set")
    print("  html-backup help            # show this help")
    print("")
    print("Available sets:")
    print("  " + ", ".join(PATH_SETS.keys()))

def parse_args(argv):
    if len(argv) == 0:
        return ("backup", None) 
    sub = argv[0].lower()
    if sub == "help":
        return ("help", None)
    if sub == "delete":
        return ("delete", argv[1] if len(argv) > 1 else None)
    if sub == "check":
        return ("check", argv[1] if len(argv) > 1 else None)
    return ("backup", argv[0])

def main():
    action, set_name = parse_args(sys.argv[1:])
    if action == "help":
        show_help()
        return

    base = Path.cwd().resolve()
    rel_paths = [normalize_rel(s) for s in collect_paths(set_name)]

    successes, failures = [], []

    if action == "backup":
        for rel in rel_paths:
            status, where, msg = backup_one(base, rel)
            (successes if status == "ok" else failures).append((where, msg))
        print(f"{BOLD}{GREEN}😎 Backed Up:{RESET}")
        for where, msg in successes:
            print(f"  - {where}: {msg}")

    elif action == "delete":
        for rel in rel_paths:
            status, where, msg = delete_in_folder(base, rel)
            (successes if status == "ok" else failures).append((where, msg))
        print(f"{BOLD}{GREEN}👋 Deleted Backups:{RESET}")
        for where, msg in successes:
            print(f"  - {where}: {msg}")

    elif action == "check":
        updated = []
        for rel in rel_paths:
            status, where, msg = check_update_one(base, rel)
            if status == "ok":
                if msg.startswith("update available"):
                    updated.append((where, msg))
            else:
                failures.append((where, msg))

        print(f"{BOLD}{YELLOW}👀 Updates Available:{RESET}")
        if updated:
            for where, msg in updated:
                print(f"  - {where}: {msg}")
        else:
            print("  none")

    if failures:
        print(f"\n{BOLD}{RED}😡 Failed:{RESET}")
        for where, reason in failures:
            print(f"  - {where}: {reason}")

if __name__ == "__main__":
    main()
