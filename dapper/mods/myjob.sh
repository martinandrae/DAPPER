#!/bin/bash
#
#SBATCH -J mscthesis
#SBATCH -t 12:00:00
#SBATCH -N 1
#SBATCH --mem=10000
#SBATCH --exclusive
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mandra@kth.se
#

module load buildenv-gcc/2018a-eb
module add Anaconda/2022.05-nsc1
cd simulation/DAPPER/dapper/mods

for i in {5..10}
do
    echo "Running QG for $i"
    conda activate dapper-env		
    python runQG.py --number $i
    conda activate processing
    python subsample_HRES.py --number $i
done


# Script ends here
