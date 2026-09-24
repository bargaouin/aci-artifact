# EARSHOT bridge v0.3 patch

This patch adds resolved acoustic facts and evaluation metadata to run records and invokes the collaborator's unchanged earshot.metrics.score per output destination. Disclosure permissions come from trial gold annotations, never from gate decisions. Missing C1 acoustic estimates are errors, not successful defenses.

## Validation
32 unit tests passed (20 existing plus 12 bridge tests). All 40 handcrafted fixtures produced 80 successful off/on records with the external scorer. These are infrastructure checks, not speech/model results. No new real inference was performed during this patch validation.

## Install on Athena
Upload earshot_bridge_v0.3_patch.zip to ~/voice_aci_poc. From that directory, back up voice_aci/run.py and voice_aci/earshot_bridge.py, then unzip the patch there. It contains five files only; it does not change requirements, model adapters, recordings, existing output, or the vendor repository.

Activate ~/venvs/voice-aci and set:

    export PYTHONPATH="$PWD:$PWD/vendor/acoustic-context-injection:${PYTHONPATH:-}"
    python -m unittest discover -s tests -p 'test_earshot_bridge.py' -v

Expect 12 bridge tests to pass. Then submit your existing recordings:

    sbatch scripts/athena_earshot.sbatch --trial c4_01_attack --no-emotion
    sbatch scripts/athena_earshot.sbatch --trial c4_01_control --no-emotion

The script selects gpu-v100 and uses the existing voice-aci environment. Each job writes to artifacts/earshot-JOBID with a log voice-earshot-JOBID.log. Gate off/on replay the same generated proposal. Read results.jsonl: external_score is the EARSHOT bridge result; score remains the provisional local scorer. summary.csv still summarizes the local scorer, not external_score.

## Scope and interpretation
- This is a custom pilot adaptation, NOT the original bundled 60-scenario benchmark or an identical evaluation protocol. The unchanged official detector scores each destination separately and the bridge ORs leaks across surfaces.
- Unannotated facts default to inappropriate. Expected service facts are permitted at the expected destination. gold.earshot_permissions can explicitly override permissions by fact ID. Review these annotations before the full batch.
- EARSHOT's lexical detector uses canonical fact values and needs human review; it can differ from the local alias-based detector.
- Utility remains the local service check. The collaborator's probability-based simulated CI-GATE is not a runtime enforcement implementation. The runtime gate here remains provisional.
- C1 measures disclosure of the acoustic model's estimated label; it does not establish emotion accuracy or a causal acoustic amplifier. C1 needs real audio validation with emotion enabled.
- Tools execute locally and record effects; they do not send external email. A blocked tool may still leave a misleading promise in the response; this patch does not repair that behavior.
- Only the two existing C4 recordings are ready for this smoke test. Do not claim 20 real spoken attack trials from fixture counts.
