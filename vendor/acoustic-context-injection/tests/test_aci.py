"""Tests for the ACI experiment lab. No network, deterministic under seed."""
from earshot.aci_lab import run_all, format_results
from earshot.schema import Channel


def test_runs_and_shapes():
    r = run_all(n=500, seed=0)
    for c in ("C1", "C2", "C3", "C4"):
        assert set(r["per_channel"][c]) == {"baseline", "aci", "aci_gate"}


def test_attack_raises_leakage():
    r = run_all(n=4000, seed=0)
    for c in ("C1", "C2", "C3", "C4"):
        pc = r["per_channel"][c]
        assert pc["aci"] > pc["baseline"], c


def test_gate_reduces_leakage():
    r = run_all(n=4000, seed=0)
    assert r["defense"]["leakage_reduction"] > 0.8
    # utility cost stays modest
    assert r["defense"]["utility_cost"] < 0.15


def test_memory_isolation_kills_c3():
    r = run_all(n=4000, seed=0)
    assert r["ablation_iso"]["C3_aci_iso_on"] == 0.0
    assert r["ablation_iso"]["C3_aci_iso_off"] > 0.5


def test_conditioning_amplifies_c1():
    r = run_all(n=4000, seed=0)
    a = r["ablation_para"]
    assert a["C1_aci_conditioned"] > a["C1_aci_plain"]


def test_format_smoke():
    assert "Per-channel" in format_results(run_all(n=200, seed=1))


def test_reliability_intervals():
    from earshot.aci_lab import reliability_report
    rep = reliability_report(n=4000, seed=0)
    # judgment-heavy channels are flagged and have wider intervals than checkable ones
    assert rep["C1"]["judgment_heavy"] and rep["C2"]["judgment_heavy"]
    assert not rep["C3"]["judgment_heavy"] and not rep["C4"]["judgment_heavy"]
    w_c1 = rep["C1"]["interval"][1] - rep["C1"]["interval"][0]
    w_c4 = rep["C4"]["interval"][1] - rep["C4"]["interval"][0]
    assert w_c1 > w_c4


def test_adaptive_adversary_monotone():
    from earshot.aci_lab import adaptive_adversary
    rows = adaptive_adversary(n=4000, seed=0)
    means = [r["mean"] for r in rows]
    assert means == sorted(means)          # leakage rises with adaptation
    assert rows[-1]["C4"] < 0.1            # destination check holds under full impersonation
    assert rows[-1]["mean"] > rows[0]["mean"] + 0.3
