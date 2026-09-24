"""Convert matching M4A recordings and validate required WAVs; never overwrite."""
import argparse
import json
import wave
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--trial')
p.add_argument('--convert', action='store_true')
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
trials=json.loads((root/'configs/trials_v04.json').read_text())
if a.trial:
    trials=[t for t in trials if t['id']==a.trial]
    if not trials: raise SystemExit('Unknown trial ID')
missing=[]
for t in trials:
    path=root/t['audio']
    source=path.with_suffix('.m4a')
    if not path.exists() and a.convert and source.exists():
        import numpy as np
        from faster_whisper.audio import decode_audio
        audio=decode_audio(str(source), sampling_rate=16000)
        if not len(audio) or not np.isfinite(audio).all():
            raise ValueError('Invalid decoded audio: '+str(source))
        pcm=(np.clip(audio,-1,1)*32767).astype('<i2').tobytes()
        with path.open('xb') as f:
            with wave.open(f,'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
                w.writeframes(pcm)
        print('CONVERTED',path.name)
    if not path.exists():
        missing.append(str(path.relative_to(root))); continue
    with wave.open(str(path),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,16000) or not w.getnframes():
            raise ValueError('Expected nonempty 16-kHz mono PCM16 WAV: '+str(path))
        print('READY',path.name,round(w.getnframes()/16000,2),'seconds')
if missing:
    print('\nMissing recordings:\n'+'\n'.join(missing))
    raise SystemExit(1)
print('All selected recordings present. Listen to each recording to check wording and quality.')
