from pathlib import Path
import re

def test_repository_contains_no_obvious_live_secrets():
    root=Path(__file__).parents[1]
    bad=[]
    patterns=[re.compile(r"\btgt_[A-Za-z0-9._-]{16,}"), re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), re.compile(r"\blsv2_[A-Za-z0-9._-]{16,}")]
    for p in root.rglob("*"):
        if p.is_file() and p.suffix not in {".zip",".png",".jpg",".pyc"} and ".git" not in p.parts and "__pycache__" not in p.parts:
            try: txt=p.read_text(errors="ignore")
            except Exception: continue
            for pattern in patterns:
                if pattern.search(txt): bad.append(str(p))
    assert not bad, f"Possible secrets in: {bad}"
