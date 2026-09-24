import csv
import json
from collections import defaultdict
from pathlib import Path


def summarize(output):
    output = Path(output)
    groups = defaultdict(list)
    for line in (output / 'results.jsonl').read_text().splitlines():
        row = json.loads(line)
        groups[(row['experiment_kind'], row['channel'], row['condition'], row['gate'])].append(row)
    summaries = []
    for key, rows in sorted(groups.items()):
        valid = [r for r in rows if r['status'] == 'ok']
        leaks = sum(r['score']['leak'] for r in valid)
        service = [r['score']['service'] for r in valid if r['score']['service'] is not None]
        summaries.append(dict(zip(['experiment_kind', 'channel', 'condition', 'gate'], key),
                              n_total=len(rows), n_valid=len(valid), n_errors=len(rows)-len(valid),
                              leaks=leaks, leak_rate_valid=leaks/len(valid) if valid else '',
                              service_successes=sum(service), service_n=len(service),
                              service_rate_valid=sum(service)/len(service) if service else '',
                              warning='ALIAS_BASED_REQUIRES_HUMAN_REVIEW; FIXTURES_ARE_NOT_MODEL_RESULTS'))
    with open(output / 'summary.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0]) if summaries else ['n_total'])
        writer.writeheader()
        writer.writerows(summaries)
    with open(output / 'review.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['trial_id', 'gate', 'status', 'asr_meaning_preserved',
                                              'human_leak', 'human_service', 'reviewer', 'notes'])
        writer.writeheader()
        for rows in groups.values():
            for r in rows:
                writer.writerow({k: r[k] for k in ['trial_id', 'gate', 'status']})

if __name__ == '__main__':
    import sys
    summarize(sys.argv[1])
