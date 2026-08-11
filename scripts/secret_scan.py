from pathlib import Path
import re, sys
root=Path(__file__).parents[1]
patterns=[r"\btgt_[A-Za-z0-9._-]{16,}",r"\bsk-[A-Za-z0-9_-]{20,}",r"\blsv2_[A-Za-z0-9._-]{16,}"]
bad=[]
for p in root.rglob('*'):
    if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts and p.suffix != '.pyc':
        try:s=p.read_text(errors='ignore')
        except:continue
        if any(re.search(x,s) for x in patterns):bad.append(str(p))
print('PASS: no obvious live secrets' if not bad else 'FAIL: '+str(bad)); sys.exit(bool(bad))
