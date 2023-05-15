#!/bin/bash

# make the script executable
chmod +x setup.sh

# create a virtual environment with python 3.8
python3.8 -m venv annotator-webapp-env

# activate the virtual environment
source annotator-webapp-env/bin/activate

# install all packages from requirements.txt
pip install -r requirements.txt
