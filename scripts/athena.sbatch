#!/bin/bash
#SBATCH --job-name=voice-aci
#SBATCH --partition=gpu-v100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --output=voice-aci-%j.log
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
source "${VOICE_ACI_VENV:-$HOME/venvs/voice-aci}/bin/activate"
export TOKENIZERS_PARALLELISM=false
run_dir="artifacts/athena-${SLURM_JOB_ID}"
python -m voice_aci.run --output "$run_dir" "$@"
python -m pip freeze > "$run_dir/requirements.lock.txt"
