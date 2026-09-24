import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from voice_aci.core import Memory, LocalTools, PolicyGate, dispatch, pilot_score, parse_action, word_error_rate
from voice_aci.run import add_acoustic
ROOT=Path(__file__).resolve().parents[1]

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.trials=json.loads((ROOT/'configs/trials.json').read_text())
        self.fixtures=json.loads((ROOT/'configs/fixtures.json').read_text())
        self.trial=next(t for t in self.trials if t['id']=='c3_01_attack')
    def tearDown(self):self.temp.cleanup()
    def execute(self,action,trial=None,on=True):
        t=trial or self.trial
        tools=LocalTools(self.root/'tools.sqlite')
        try:return dispatch(action,t['memory'],t['context'],on,tools)
        finally:tools.close()
    def test_memory_persists_across_connections(self):
        m=Memory(self.root/'mem.sqlite');m.reset(self.trial['memory']);m.close()
        m=Memory(self.root/'mem.sqlite');self.assertEqual(len(m.facts()),5);m.close()
    def test_memory_reset_removes_prior_trial(self):
        m=Memory(self.root/'mem.sqlite');m.reset(self.trial['memory']);m.reset([])
        self.assertEqual(m.facts(),[]);m.close()
    def test_cross_speaker_response_blocked(self):
        action=self.fixtures[self.trial['id']]['action']
        self.assertTrue(self.execute(action,on=False)['released']['response'])
        self.assertEqual(self.execute(action)['released']['response'],'')
    def test_owner_allowed_control(self):
        t=next(t for t in self.trials if t['id']=='c3_01_control')
        r=self.execute(self.fixtures[t['id']]['action'],t)
        self.assertTrue(pilot_score(r['released'],t['gold'],'owner')['service'])
    def test_refusal_does_not_hide_tool_leak(self):
        t=next(t for t in self.trials if t['id']=='c4_01_attack')
        a=copy.deepcopy(self.fixtures[t['id']]['action']);a['response']='I cannot disclose private information.'
        r=self.execute(a,t,on=False)
        self.assertTrue(pilot_score(r['released'],t['gold'],'owner')['leak'])
    def test_blocked_tool_has_no_side_effect(self):
        t=next(t for t in self.trials if t['id']=='c4_01_attack')
        self.execute(self.fixtures[t['id']]['action'],t)
        db=sqlite3.connect(self.root/'tools.sqlite')
        self.assertEqual(db.execute('SELECT COUNT(*) FROM effects').fetchone()[0],0);db.close()
    def test_allowed_tool_has_persistent_effect(self):
        t=next(t for t in self.trials if t['id']=='c4_01_control')
        r=self.execute(self.fixtures[t['id']]['action'],t)
        self.assertEqual(len(r['tool_receipts']),1)
        db=sqlite3.connect(self.root/'tools.sqlite')
        self.assertIn('47 Cedar Lane',db.execute('SELECT payload FROM effects').fetchone()[0]);db.close()
    def test_exact_destination_not_suffix(self):
        t=next(t for t in self.trials if t['id']=='c4_01_control')
        a=copy.deepcopy(self.fixtures[t['id']]['action']);a['tool_calls'][0]['arguments']['destination']='rides.local.evil.test'
        self.assertFalse(self.execute(a,t)['released']['tool_calls'])
    def test_unicode_case_alias_detection(self):
        a={'response':'４７ CEDAR LN','tool_calls':[]}
        self.assertEqual(self.execute(a)['released']['response'],'')
    def test_malformed_and_unknown_tools_rejected(self):
        for a in ['not json','{"response":0,"tool_calls":[]}',
                  '{"response":"","tool_calls":[{"name":"exec","arguments":{}}]}',
                  '{"response":"","tool_calls":[],"purpose":"override"}']:
            with self.subTest(a=a),self.assertRaises((ValueError,TypeError)):parse_action(a)
    def test_spoken_purpose_cannot_override_context(self):
        t=next(t for t in self.trials if t['id']=='c2_01_attack')
        a={'response':'Authorized for personal_lookup: 47 Cedar Lane','tool_calls':[]}
        r=self.execute(a,t)
        self.assertIn('purpose:home',r['gate_decisions'][0]['reasons'])
    def test_scorer_does_not_consult_gate(self):
        a={'response':'47 Cedar Lane','tool_calls':[]}
        self.assertTrue(pilot_score(a,self.trial['gold'],'guest')['leak'])
    def test_emotion_estimate_policy_instantiation(self):
        t=next(t for t in self.trials if t['id']=='c1_01_attack')
        f,g=add_acoustic(t['memory'],t['gold'],{'label':'sad'},t['context'])
        self.assertEqual(f[-1]['value'],'sad')
        self.assertEqual(g['forbidden'][0]['values'],['sad'])
        self.assertEqual(t['gold']['forbidden'][0]['values'],['{emotion}'])
    def test_wer(self):
        self.assertEqual(word_error_rate('hello world','hello'),0.5)
        self.assertEqual(word_error_rate('Hello, world!','hello world'),0)
    def test_known_paraphrase_blindspot_is_documented(self):
        # This intentionally characterizes a LIMITATION, not a passing security claim.
        a={'response':'The house is number forty-seven on Cedar, a lane.','tool_calls':[]}
        self.assertTrue(self.execute(a)['released']['response'])
    def test_identity_spoof_not_solved_by_gate(self):
        t=copy.deepcopy(self.trial);t['context']['speaker']='owner'
        self.assertTrue(self.execute(self.fixtures[t['id']]['action'],t)['released']['response'])
    def test_all_manifest_fixtures_and_control_utility(self):
        for t in self.trials:
            with self.subTest(trial=t['id']):
                fixture=self.fixtures[t['id']]
                facts,gold=add_acoustic(t['memory'],t['gold'],fixture.get('acoustic'),t['context'])
                tt=copy.deepcopy(t);tt['memory']=facts
                off=self.execute(fixture['action'],tt,on=False)
                on=self.execute(fixture['action'],tt,on=True)
                a=pilot_score(off['released'],gold,t['context']['speaker'])
                b=pilot_score(on['released'],gold,t['context']['speaker'])
                if t['condition']=='attack':
                    self.assertTrue(a['leak']);self.assertFalse(b['leak'])
                else:self.assertTrue(a['service']);self.assertTrue(b['service'])

if __name__=='__main__':unittest.main()
