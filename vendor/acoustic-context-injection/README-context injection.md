# Acoustic Context Injection

An attack, a measurement harness, and a defense for privacy leakage through the
actions of agentic voice assistants.

This repository is the research artifact for the paper:

> **Acoustic Context Injection: Privacy Leakage Through the Actions of Agentic
> Voice Assistants.** Submitted to the Symposium on Security and Privacy in
> Speech Communication (SPSC) 2026, long-paper track. Under double-blind review;
> the author identity is withheld throughout `paper/` and this repository.

A voice assistant can leak private information not through what it says but
through what it does. Because a malicious instruction can enter through the audio
channel, neither signal anonymization, which only rewrites the speaker's timbre,
nor a text-side filter on the transcript, which sees the instruction only after
it has been decoded, ever inspects it. The leak then leaves through the agent's
own tool call.

## What is in this repository

- **Earshot**, a model-agnostic harness that scores privacy leakage by the
  agent's action rather than its wording, across four channels.
- **Acoustic Context Injection (ACI)**, an attack whose payload is decoded from
  audio and carried out by the agent's own tool calls.
- **CI-Gate**, a runtime contextual-integrity tool gate that checks speaker of
  record, purpose, and destination before a privileged action.
- The paper source, the scenario data, the frozen results, and the test suite.

The four channels are C1 paralinguistic self-inference, where the agent reads an
attribute such as age, emotion, or health from the voice and acts on it; C2
autonomous disclosure, where the agent volunteers private context nobody asked
for; C3 cross-speaker memory bleed, where one speaker's remembered data surfaces
to another on a shared device; and C4 tool-call exfiltration, where private
context leaves inside a tool call whose destination the adversary influences.

## What the numbers are, and are not

Every rate reported here is a property of a calibrated reference agent, defined
in `earshot/aci_lab.py`, whose action probabilities are set explicitly and
calibrated to published disclosure and injection rates. The numbers are stated
as properties of that reference agent and are never attributed to any commercial
model. No recorded speech and no personal data are used. The same harness runs
unchanged on a real speech model or a cascade through the adapters in
`earshot/adapters.py`; supplying credentials produces the same measurements with
real rates in place of calibrated ones. Running a live attack against a third
party's deployed assistant raises consent and disclosure questions that a
measurement paper should not answer unilaterally, which is why the released
artifact measures rather than weaponizes.

## Repository layout

```
earshot/            the Earshot harness (pure Python standard library)
  schema.py         scenario, fact, and response types
  scenarios.py      the contextual-integrity probe scenarios
  adapters.py       model adapters (stub, and real-model interfaces)
  judge.py          the action-level leak judge
  metrics.py        leakage, service, and attack-success scoring
  runner.py         run a model over the scenarios and score it
  aci_lab.py        reference agent, ACI attack, CI-Gate, and all experiments
  __main__.py       command-line entry point
data/               inputs and frozen outputs (see data/README.md)
  scenarios.json    the 60 scenarios in machine-readable form
  results_aci.json  the exact reference-agent run behind the paper's numbers
scripts/
  export_data.py    regenerate the contents of data/
tests/              unit tests, including the ACI invariants
paper/              LaTeX source and the compiled preview of the paper
```

## Installation

The harness has no third-party dependencies. Python 3.10 or newer is required.

```
git clone <repository-url>
cd acoustic-context-injection
pip install -e .
```

## Quickstart

Run the harness on the bundled scenarios with the deterministic stub agent:

```
python -m earshot
```

Or from Python:

```python
from earshot import run, format_report, ADAPTERS
report = run(ADAPTERS["stub"])
print(format_report(report))
```

## Reproducing the paper

The reference-agent experiments are deterministic at a fixed seed. To reproduce
every table and figure:

```
python -m earshot.aci_lab
```

This prints the per-channel rates, the delivery grid, the defense results, the
ablations, the reliability intervals, the adaptive-adversary sweep, the gate
frontier, the judge validation, and the paralinguistic probe, and writes them to
`aci_results.json`. The same content, pretty-printed, is committed at
`data/results_aci.json`. Individual results are also available directly:

```python
from earshot.aci_lab import (
    run_all, reliability_report, adaptive_adversary,
    sweep_gate, judge_validation, paralinguistic_test,
)
print(run_all())                 # per-channel baseline, ACI, ACI+CI-Gate
print(reliability_report())      # per-channel reliability intervals
print(adaptive_adversary())      # gated leakage under owner impersonation
print(judge_validation())        # judge-versus-human agreement per channel
```

The headline numbers, all on the reference agent at 6000 trials per cell: ACI
raises mean leakage across the four channels from 0.21 to 0.64; CI-Gate cuts mean
leakage to 0.02, a 96.9 percent reduction, at a 5.8 percent cost in legitimate
requests; memory isolation drives the cross-speaker channel to 0.00; and under
full owner impersonation the gate's speaker and purpose checks return to attack
levels while the destination check holds C4 at 0.02.

## Running on a real model

`earshot/adapters.py` exposes a single adapter interface: a callable that maps a
scenario to an `AgentResponse`. The stub adapter is the calibrated reference
agent. To measure a real system, implement or configure an adapter that calls
your model, supply credentials through your environment, and pass it to `run`.
The scenarios, the judge, and the metrics are unchanged, so the output is the
same schema with measured rates.

## Tests

```
python -m pytest
```

The suite includes the ACI invariants behind the paper: the attack raises
leakage on every channel, the gate cuts mean leakage by more than 80 percent at
modest utility cost, memory isolation eliminates the cross-speaker channel,
paralinguistic conditioning amplifies C1, the judgment-heavy channels carry
wider reliability intervals than the locally checkable ones, and gated leakage
rises monotonically with the adversary's ability to impersonate the owner while
the destination check holds. The same tests run in continuous integration across
Python 3.10 to 3.12 (`.github/workflows/ci.yml`).

## Building the paper

```
cd paper
pdflatex main_compilecheck.tex
bibtex   main_compilecheck
pdflatex main_compilecheck.tex
pdflatex main_compilecheck.tex
```

`main_compilecheck.tex` is a portable build that compiles anywhere;
`main_compilecheck.pdf` is the verified output. For submission, `main.tex`
targets the official Interspeech 2026 kit and is compiled with that kit in place.

## Citation

See `CITATION.cff`. The paper is under double-blind review, so please cite the
venue and title until the camera-ready author list is public.

## License

MIT. See `LICENSE`.
