#!/bin/bash
#
#SBATCH -J mscthesiswork
#SBATCH -t 06:00:00
#SBATCH -N 1
#SBATCH --mem=10000
#SBATCH --exclusive
#SBATCH --mail-type=ALL
#SBATCH --mail-user=mandra@kth.se
#
module load buildenv-gcc/2018a-eb
module add Anaconda/2022.05-nsc1
conda activate dapper-env		
cd simulation/DAPPER/dapper/mods
python runQG.py
conda activate processing
python subsample_HRES.py

# Script ends here
