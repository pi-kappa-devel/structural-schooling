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

cluster=`hostname`
if [[ $cluster == "safe-gpu01" ]]
then
    echo "Loading SAFE configuration."
    spack load python@3.11.2
    spack load py-numpy@1.24.3
    spack load py-scipy@1.10.1
elif [[ $cluster == "fuchs.cm.cluster" ]]
then
    echo "Loading FUCHS configuration."
    spack load python@3.9.9%gcc@11.2.0 arch=linux-scientific7-ivybridge
    spack load py-numpy@1.22.1%gcc@11.2.0 arch=linux-scientific7-ivybridge
    spack load py-scipy@1.7.3%gcc@11.2.0 arch=linux-scientific7-ivybridge
elif [[ $cluster =~ login0[1-2].cm.cluster ]]
then
    echo "Loading HHLR configuration."
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
    `python -c 'import calibration_traits; print(*calibration_traits.setups().keys())'`
)

# Calibration income group
declare -a group_array=(
    `python -c 'import model_traits; print(*model_traits.income_groups())'`
)

# Prepare tasks to be executed
declare -a tasks=()
for setup in "${setup_array[@]}"; do
    for group in "${group_array[@]}"; do
        paths="-o ../out.$timestamp -l ../log.$timestamp -r ../res.$timestamp"
        task="python calibration.py -s $setup -g $group $paths"
        message="echo 'Finished task $setup-$group.'"
        tasks+=("$task && $message")
    done
done

# Execute tasks
printf '%s\n' "${tasks[@]}" | xargs --max-procs=$procs -n 1 -I {} bash -c '{}'

# Wait for all child processes to terminate.
wait


