# Validation record

Executed locally: 20 unittest tests passed (17 core tests, 3 runner tests). Full output is in test-output.txt.

Executed fixture batch: 40 scripted scenarios, each replayed with gate off and on, yielding 80 successful infrastructure records and no duplicate trial/condition keys. These are handcrafted actions and fixture transcripts, NOT speech or LLM outputs. The fixture suite includes 20 attacks and 20 controls. Expected fixture behavior was asserted, including gate-off disclosure, blocked gate-on disclosure, and allowed legitimate controls.

Syntax checks: Python compileall passed; bash -n scripts/athena.sbatch passed.

Specific failure checks: unknown tools and malformed JSON rejected; existing output preserved; external scorer failure creates error records without duplicate success rows; blocked tools leave no SQLite side effects. Tests explicitly demonstrate the paraphrase blind spot and dependence on supplied speaker identity.

Not executed: Whisper transcription, Qwen generation, HuBERT inference, GPU/Slurm execution, recorded or synthesized utterances, original EARSHOT integration. The build environment lacks these model packages and a GPU. Their adapters follow official documented interfaces but require runtime validation on Athena.

Scientific status: no real-audio attack-success rate, no measured gate reduction, no measured utility cost, and no evidence yet that acoustic conditioning increases attack success. Pilot scoring requires independent manual review and alignment with the original harness.
