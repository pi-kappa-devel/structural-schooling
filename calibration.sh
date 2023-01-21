#!/bin/bash
#SBATCH --job-name=structural-schooling
#SBATCH --partition=fuchs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --mem-per-cpu=3072
#SBATCH --time=48:00:00
#SBATCH --no-requeue
#SBATCH --mail-type=NONE
#SBATCH --account=agmisc


# Number of processes to be simultaneously executed
export procs=`expr $(nproc --all)`

# Calibration setup array
declare -a setup_array=(
    `python -c 'import calibration_mode; print(*calibration_mode.mapping().keys())'`
)

# Prepare tasks to be executed
declare -a tasks=()
for setup in "${setup_array[@]}"; do
    tasks+=("python calibration.py -m $setup")
done

# Execute tasks
printf '%s\n' "${tasks[@]}" | xargs --max-procs=$procs -n 1 -I {} bash -c '{}'

# Wait for all child processes to terminate.
wait


