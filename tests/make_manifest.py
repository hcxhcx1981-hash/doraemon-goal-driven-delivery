"""Generate SHA256 manifest for the distribution (UTF-8, no BOM).

Lists every package file under the DIST top-level directory name (== skill
name) with its SHA256, one line per file, so a consumer can re-verify after
extraction. Run AFTER the final file set is frozen.
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    dist_dir = sys.argv[1] if len(sys.argv) > 1 else str(ROOT)
    top = Path(dist_dir).name if len(Path(dist_dir).parts) > 1 else None
    base = Path(dist_dir)
    lines = []
    files = []
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if any(part in {".git", "__pycache__"} for part in p.relative_to(base).parts):
            continue
        if p.name == "SHA256_MANIFEST.txt":
            continue
        files.append(p)
    for p in files:
        rel = p.relative_to(base).as_posix()
        h = hashlib.sha256(p.read_bytes()).hexdigest().upper()
        lines.append(f"{h}  {rel}")
    out = base / "SHA256_MANIFEST.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")  # no BOM
    print(f"MANIFEST: {len(files)} files -> {out}")


if __name__ == "__main__":
    main()
