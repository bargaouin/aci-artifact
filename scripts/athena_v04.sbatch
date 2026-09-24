#!/bin/bash
#SBATCH --job-name=voice-v04
#SBATCH --partition=gpu-v100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=voice-v04-%j.log
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source "${VOICE_ACI_VENV:-$HOME/venvs/voice-aci}/bin/activate"
export PYTHONPATH="$PWD:$PWD/vendor/acoustic-context-injection:${PYTHONPATH:-}"
export TOKENIZERS_PARALLELISM=false
selected=()
if [ "$#" -gt 1 ]; then
    echo 'Usage: sbatch scripts/athena_v04.sbatch [trial_id]'
    exit 2
fi
if [ "$#" -eq 1 ]; then selected=(--trial "$1"); fi
python scripts/prepare_audio_v04.py "${selected[@]}"
# HuBERT stays enabled: C1 cannot run with --no-emotion.
python -m voice_aci.run --manifest configs/trials_v04.json \
    --output "artifacts/v04-${SLURM_JOB_ID}" \
    --external-scorer voice_aci.earshot_bridge:score "${selected[@]}"
python -m pip freeze > "artifacts/v04-${SLURM_JOB_ID}/requirements.lock.txt"
