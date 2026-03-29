from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ocw_workbench.utils.release_assets import (
    build_checksum_file,
    build_workbench_archive,
    checksum_file_name,
    collect_release_files,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build OCW GitHub release assets.")
    parser.add_argument("--tag", required=True, help="Release tag, for example v0.1.0")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--dist-dir", default="dist/release", help="Output directory for extra release assets")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    dist_dir = (repo_root / args.dist_dir).resolve() if not Path(args.dist_dir).is_absolute() else Path(args.dist_dir).resolve()

    archive_path = build_workbench_archive(repo_root, dist_dir, args.tag)
    checksum_path = build_checksum_file(
        collect_release_files(repo_root, archive_path),
        dist_dir / checksum_file_name(args.tag),
    )

    print(archive_path)
    print(checksum_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
