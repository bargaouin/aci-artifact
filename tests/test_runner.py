import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class RunnerTests(unittest.TestCase):
    def invoke(self,out,*extra,env=None):
        return subprocess.run([sys.executable,'-m','voice_aci.run','--mode','fixture','--trial','c4_01_attack',
                               '--output',str(out),*extra],cwd=ROOT,text=True,capture_output=True,env=env)
    def test_malformed_action_is_error_not_gate_success(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); fixture=p/'bad.json'
            fixture.write_text(json.dumps({'c4_01_attack':{'action':{'response':10,'tool_calls':[]}}}))
            result=self.invoke(p/'out','--fixtures',str(fixture))
            self.assertNotEqual(result.returncode,0)
            records=[json.loads(x) for x in (p/'out/results.jsonl').read_text().splitlines()]
            self.assertEqual(len(records),2)
            self.assertTrue(all(x['status']=='error' and 'score' not in x for x in records))
    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            marker=Path(d)/'keep';marker.write_text('preserve')
            result=self.invoke(d)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual(marker.read_text(),'preserve')
    def test_external_scorer_failure_does_not_duplicate_success_row(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'broken_scorer.py').write_text("def score(trial, record):\n    if record['gate']=='on': raise ValueError('test failure')\n    return {'ok':True}\n")
            env=dict(os.environ);env['PYTHONPATH']=str(p)+os.pathsep+str(ROOT)
            result=self.invoke(p/'out','--external-scorer','broken_scorer:score',env=env)
            self.assertNotEqual(result.returncode,0)
            records=[json.loads(x) for x in (p/'out/results.jsonl').read_text().splitlines()]
            self.assertEqual(len(records),2)
            self.assertTrue(all(x['status']=='error' for x in records))

if __name__=='__main__':unittest.main()
