#!/bin/bash
#SBATCH --job-name=structural-schooling
#SBATCH --partition=fuchs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --mem-per-cpu=3072
#SBATCH --time=48:00:00
#SBATCH --no-requeue
#SBATCH --mail-type=ALL
#SBATCH --account=agmisc

architecture=`cat /sys/devices/cpu/caps/pmu_name`
echo "Loading $architecture libraries."
if [[ $architecture == "ivybridge" ]]
then
    spack load python@3.9.9%gcc@11.2.0 arch=linux-scientific7-ivybridge
    spack load py-numpy@1.22.1%gcc@11.2.0 arch=linux-scientific7-ivybridge
    spack load py-scipy@1.7.3%gcc@11.2.0 arch=linux-scientific7-ivybridge
elif [[ $architecture == "skylake_avx512" ]]
then
    spack load python@3.9.9%gcc@11.2.0 arch=linux-scientific7-skylake_avx512
    spack load py-numpy@1.22.1%gcc@11.2.0 arch=linux-scientific7-skylake_avx512
    spack load py-scipy@1.7.3%gcc@11.2.0 arch=linux-scientific7-skylake_avx512
fi

# Execution timestamp
timestamp=$(date +%Y%m%d%H%M%S)

# Number of processes to be simultaneously executed
export procs=`expr $(nproc --all)`

# Calibration setup array
declare -a setup_array=(
    `python -c 'import calibration_mode; print(*calibration_mode.mapping().keys())'`
)

# Prepare tasks to be executed
declare -a tasks=()
for setup in "${setup_array[@]}"; do
    task="python calibration.py -m $setup -r ./out.$timestamp -l ./log.$timestamp"
    message="echo 'Finished task $setup.'"
    tasks+=("$task && $message")
done

# Execute tasks
printf '%s\n' "${tasks[@]}" | xargs --max-procs=$procs -n 1 -I {} bash -c '{}'

# Wait for all child processes to terminate.
wait


