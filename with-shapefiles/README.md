# Satellite Processing (with shapefiles)
Rutgers Center for Ocean Observing Leadership tools to manage and plot satellite data (including shapefiles e.g. BOEM leasing areas on surface maps).

## Installation Instructions
Add the channel conda-forge to your .condarc. You can find out more about conda-forge from their website: https://conda-forge.org/

`conda config --add channels conda-forge`

Clone the satellite-processing repository

`git clone https://github.com/rucool/satellite-processing.git`

Change your current working directory to the location that you downloaded satellite-processing with-shapefiles. 

`cd /Users/lgarzio/Documents/repo/satellite-processing/with-shapefiles`

Create conda environment from the included environment.yml file:

`conda env create -f environment.yml`

Once the environment is done building, activate the environment:

`conda activate satellite-processing-with-sf`

Install the toolbox to the conda environment from the root directory of the satellite-processing with-shapefiles toolbox:

`pip install .`

The toolbox should now be installed to your conda environment.