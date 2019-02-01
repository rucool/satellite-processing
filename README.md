# Satellite Processing
Rutgers Center for Ocean Observing Leadership tools to manage and plot satellite data.

## Installation Instructions
Add the channel, conda-forge, to your .condarc. You can find out more about conda-forge from their website: https://conda-forge.org/

`conda config --add channels conda-forge`

Clone the satellite-processing repository

'git clone https://github.com/rucool/satellite-processing.git'

Change your current working directory to the location that you downloaded satellite-processing. 

`cd /Users/lgarzio/Documents/repo/satellite-processing/`

Create conda environment from the included environment.yml file:

`conda env create -f environment.yml`

Once the environment is done building, activate the environment:

'conda activate satellite-processing'

Install the toolbox to the conda environment from the root directory of the satellite-processing toolbox:

'pip install .'

The toolbox should now be installed to your conda environment.

## Folders
### coldest_pixel
Contains tools for producing netCDF files containing the daily coldest pixel composite using NOAA-AVHRR satellite SST declouded based on reflectivity in the visible spectrum. This method of declouding is limited to daylight hours, but lets in cold water that often gets flagged as clouds based on other declouding algorithms, making this product a useful tool for identifying upwelling regions and storm cooling earlier than they are typically seen in other SST products.

### functions
Contains common functions used by multiple tools

### plotting
Contains tools for plotting data