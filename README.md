DiffractionLimitedAnalysis
===============

Rapid diffraction limited image analysis program.

Copyright 2021 Zengjie Xia, at the University of Cambridge

DiffractionLimitedAnalysis is intended for rapid analysis of diffraction limited images, to distinguish the protein aggregates (or other targets) captured by the SimPull surface. The image processing part of this code relies on [Fiji(is just imagej)](https://imagej.net/Fiji) and [ComDet](https://github.com/ekatrukha/ComDet) - a plugin written by Eugene Katrukha at the Utrecht University.

Requirements
------------

- Python 3 (tested with Python 3.6-3.9)
	- os
	- sys
	- re
	- tqdm
	- astropy (updated 19/05/2021)
	- PIL (updated 19/05/2021)
	- scipy (updated 19/05/2021)
	- [numpy](https://numpy.org/)
	- [pandas](https://pandas.pydata.org/)
	- [scikit-image](https://scikit-image.org/)
	- [PySide 6](https://pypi.org/project/PySide6/)
	- [pyqtgraph](https://github.com/pyqtgraph/pyqtgraph)
    - [pyimagej](https://github.com/imagej/pyimagej) (install with conda-forge)

- [Fiji(is just imagej)](https://imagej.net/Fiji) 
	- [ComDet](https://github.com/ekatrukha/ComDet)

Installation
------------
Please install Anaconda for environment management.
```sh
cd /path-to-folder/
setup_conda_env.bat
```

Usage
-----
*The program only support windows system for now*

Command line tool:
```sh
conda activate DLA_python3
python /path_to/main.py
```
