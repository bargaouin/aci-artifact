"""Check all manifest paths before booking GPU time. No model dependencies."""
import json
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
trials = json.loads((root / 'configs/trials.json').read_text())
missing = [t['audio'] for t in trials if not (root / t['audio']).is_file()]
print(f'{len(trials)-len(missing)}/{len(trials)} audio files present')
for path in missing:
    print('MISSING', path)
sys.exit(bool(missing))
