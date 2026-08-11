import json
from reality_handoff.replay import run_replay
print(json.dumps(run_replay(task="inspect canonical customer orders"),indent=2))
