from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import importlib.metadata
import json
import platform
import time
from pathlib import Path
from .core import Memory, LocalTools, dispatch, pilot_score, parse_action, word_error_rate


def append(path, row):
    with open(path, 'a') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')


def add_acoustic(facts, gold, acoustic, context):
    facts, gold = copy.deepcopy(facts), copy.deepcopy(gold)
    if acoustic:
        value = acoustic['label']
        facts.append({'id': 'voice_emotion', 'owner': context['speaker'], 'value': value, 'aliases': [],
                      'purposes': ['emotion_feedback'], 'destinations': ['speaker:' + context['speaker']]})
        # Annotation instantiation uses the model estimate, not a true emotion label.
        # Scoring concerns unauthorized release of the estimate, not classifier accuracy.
        def replace(obj):
            if isinstance(obj, str):
                return obj.replace('{emotion}', value)
            if isinstance(obj, list):
                return [replace(x) for x in obj]
            if isinstance(obj, dict):
                return {k: replace(v) for k, v in obj.items()}
            return obj
        gold = replace(gold)
    return facts, gold


def run(args):
    root = Path(args.manifest).resolve().parent.parent
    manifest_bytes = Path(args.manifest).read_bytes()
    trials = json.loads(manifest_bytes)
    if args.trial:
        trials = [t for t in trials if t['id'] == args.trial]
        if not trials:
            raise ValueError('Unknown trial ID')
    out = Path(args.output)
    if out.exists():
        raise FileExistsError('Use a new output directory to avoid mixing experiments')
    out.mkdir(parents=True)
    scorer = None
    if args.external_scorer:
        module, name = args.external_scorer.split(':', 1)
        scorer = getattr(importlib.import_module(module), name)
    fixtures = json.loads(Path(args.fixtures).read_text()) if args.mode == 'fixture' else None
    asr = agent = emotion = None
    metadata = {'mode': args.mode, 'experiment_kind': 'synthetic_integration_test' if fixtures is not None else 'real_audio_model_pilot',
                'python': platform.python_version(), 'platform': platform.platform(), 'seed': args.seed,
                'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(), 'args': vars(args),
                'pairing': 'same_generated_proposal_replayed_off_and_on',
                'speaker_identity': 'externally_supplied_NOT_voice_authenticated',
                'packages': {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}}
    if fixtures is None:
        from .models import WhisperASR, LocalAgent, EmotionModel
        import random
        import torch
        random.seed(args.seed)
        torch.manual_seed(args.seed)
        asr = WhisperASR(args.asr_model, args.asr_revision, args.asr_device)
        agent = LocalAgent(args.agent_model, args.agent_revision, args.device)
        if not args.no_emotion:
            emotion = EmotionModel(args.emotion_model, args.emotion_revision)
        metadata['models'] = {'asr': asr.metadata, 'agent': agent.metadata,
                              'emotion': emotion.metadata if emotion else None}
        metadata['gpu'] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    (out / 'manifest.json').write_bytes(manifest_bytes)
    for trial in trials:
        start = time.monotonic()
        trial_dir = out / trial['id']
        trial_dir.mkdir()
        base = {'trial_id': trial['id'], 'pair_id': trial['pair_id'], 'channel': trial['channel'],
                'condition': trial['condition'], 'mode': args.mode,
                'experiment_kind': metadata['experiment_kind'], 'context': trial['context']}
        try:
            if fixtures is not None:
                fixture = fixtures[trial['id']]
                transcript = {'text': trial['utterance'], 'source': 'fixture_NOT_ASR'}
                acoustic = fixture.get('acoustic')
                raw = json.dumps(fixture['action'])
                messages = None
                audio_hash = None
            else:
                audio = root / trial['audio']
                if not audio.exists():
                    raise FileNotFoundError(str(audio))
                if trial['channel'] == 'C1' and emotion is None:
                    raise ValueError('C1 requires measured acoustic features; cannot silently use text only')
                audio_hash = hashlib.sha256(audio.read_bytes()).hexdigest()
                transcript = asr.transcribe(audio)
                if not transcript['text'].strip():
                    raise ValueError('Empty ASR transcript; trial is not a successful defense')
                acoustic = emotion.classify(audio) if trial['channel'] == 'C1' else None
                facts, gold = add_acoustic(trial['memory'], trial['gold'], acoustic, trial['context'])
                memory = Memory(trial_dir / 'memory.sqlite')
                try:
                    memory.reset(facts)
                    raw, messages = agent.act(transcript['text'], memory.facts(), trial['context'], acoustic)
                finally:
                    memory.close()
            facts, gold = add_acoustic(trial['memory'], trial['gold'], acoustic, trial['context'])
            proposal = {'transcript': transcript, 'audio_sha256': audio_hash, 'acoustic': acoustic,
                        'raw_output': raw, 'messages': messages, 'gold': gold,
                        'wer': word_error_rate(trial['utterance'], transcript['text'])}
            (trial_dir / 'proposal.json').write_text(json.dumps(proposal, indent=2))
            action = parse_action(raw)
            completed_rows = []
            for gate in ('off', 'on'):
                # Separate persistent snapshots and tool effects for each condition.
                mem = Memory(trial_dir / (gate + '_memory.sqlite'))
                tool = LocalTools(trial_dir / (gate + '_tools.sqlite'))
                try:
                    mem.reset(facts)
                    result = dispatch(action, mem.facts(), trial['context'], gate == 'on', tool)
                    scores = pilot_score(result['released'], gold, trial['context']['speaker'])
                    row = {**base, 'gate': gate, 'status': 'ok', 'proposal': action, **result,
                           'score': scores, 'wer': proposal['wer'], 'audio_sha256': audio_hash,
                           'elapsed_seconds': time.monotonic() - start}
                    row['acoustic'] = acoustic
                    row['evaluation'] = {'facts': facts, 'gold': gold,
                                         'transcript': transcript['text']}
                    if scorer:
                        # External plug-in receives full record; never changes local scoring invisibly.
                        row['external_score'] = scorer(copy.deepcopy(trial), copy.deepcopy(row))
                    completed_rows.append(row)
                finally:
                    mem.close()
                    tool.close()
            for row in completed_rows:
                append(out / 'results.jsonl', row)
        except Exception as exc:
            append(out / 'errors.jsonl', {**base, 'error_type': type(exc).__name__, 'error': str(exc)})
            # Errors are retained; never counted as successful defenses.
            for gate in ('off', 'on'):
                append(out / 'results.jsonl', {**base, 'gate': gate, 'status': 'error',
                                             'error_type': type(exc).__name__, 'error': str(exc)})
    from .summarize import summarize
    summarize(out)
    print('Results:', out.resolve())
    if (out / 'errors.jsonl').exists():
        raise SystemExit('Some trials failed; inspect errors.jsonl. No failed trial counts as a defense success.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', default='configs/trials.json')
    p.add_argument('--output', required=True)
    p.add_argument('--mode', choices=['real', 'fixture'], default='real')
    p.add_argument('--fixtures', default='configs/fixtures.json')
    p.add_argument('--trial')
    p.add_argument('--asr-model', default='Systran/faster-whisper-small')
    p.add_argument('--asr-revision')
    p.add_argument('--asr-device', choices=['cpu', 'cuda'], default='cpu')
    p.add_argument('--agent-model', default='Qwen/Qwen2.5-7B-Instruct')
    p.add_argument('--agent-revision')
    p.add_argument('--device', choices=['cpu', 'cuda'], default='cuda')
    p.add_argument('--emotion-model', default='superb/hubert-large-superb-er')
    p.add_argument('--emotion-revision')
    p.add_argument('--no-emotion', action='store_true')
    p.add_argument('--external-scorer', help='Importable module:function accepting (trial, record)')
    p.add_argument('--seed', type=int, default=0)
    run(p.parse_args())

if __name__ == '__main__':
    main()
