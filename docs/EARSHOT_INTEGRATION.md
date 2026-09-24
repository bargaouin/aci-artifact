# Adapter handoff for the existing EARSHOT harness

The current provisional scorer is `voice_aci.core.pilot_score`. It is independent of the gate, but uses exact/alias annotations. It is not a claim of EARSHOT equivalence.

Please obtain:
1. The repository/ZIP and commit corresponding to the paper.
2. A scenario example and action trace with its expected score.
3. The scorer entry point, dependencies, and judge configuration.
4. CI-GATE source or its exact authorization schema and matching procedure.
5. Existing model adapter signatures, if any.
6. One reproduction command and expected output.

An external scorer can be attached without modifying the local scorer:

```bash
python -m voice_aci.run --output artifacts/earshot-run --external-scorer my_adapter:score
```

The importable callable receives `(trial: dict, record: dict)` and must return a JSON-serializable score. `record` contains `proposal`, `released`, `tool_receipts`, `gate_decisions`, `context`, `mode`, and the provisional `score`. `trial` holds evaluation-only `gold`, scenario metadata, and the memory fixture. The runner stores the returned result under `external_score`. The provisional summary is NOT automatically replaced; an EARSHOT-specific report must use the official metric definitions and denominators after integration.

Do not invent her expected schema. Map to it after receiving an actual example. Verify agreement on hand-labeled controls and a refusal-plus-tool-leak trace. Check whether her scorer requires semantic judgments, destination provenance, action timing, or richer multi-turn traces. Add those fields where necessary.

The gate integration is a separate task from scorer integration. The local `PolicyGate` is deliberately named as a reimplementation. Preserve raw proposals and actual released actions when replacing it, and regression-test the fixed-action paired replay.
