from pathlib import Path
import re
import sys

root = Path(__file__).parents[1]
patterns = [
    re.compile(r"\btgt_[A-Za-z0-9._-]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\blsv2_[A-Za-z0-9._-]{16,}"),
    # JWT-like bearer/PAT values, including DataHub OSS personal tokens.
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
]

bad = []
for path in root.rglob("*"):
    if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
        continue
    if path.suffix in {".pyc", ".zip", ".png", ".jpg", ".jpeg", ".webp"}:
        continue
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        continue
    if any(pattern.search(text) for pattern in patterns):
        bad.append(str(path.relative_to(root)))

if bad:
    print("FAIL: possible live secrets in " + ", ".join(sorted(bad)))
    raise SystemExit(1)
print("PASS: no obvious live secrets")
