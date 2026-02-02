# Exploratory Data Analysis (EDA) 

## Overview

This project provides modular, resusable Python Scripts for performing Exploratory Data Analysis on tabular datasets. It is designed to support early stage data understanding, validation, and profiling before downstream analystics, modelling, or pipeline development.
The toolkit automates common but essential EDA tasks such as:

    -Row, column, Null and duplicate counts
    -Summary Statistics (Maximum, Minimum, median, Standard deviation)
    -Outlier detection
    
By understanding these analysis, the project inproves consistency, reproducibility, and efficiency, expecially in collaborative and production-adjacent data workflows.

---

## Initial setup.
    1. Clone the repository on GitHub or Gitlab to your local computer
    2. Use an Integrated Development Environment (IDE)
    3. Create a virtual environment
    4. Make sure Python is installed and also install the dependencies (Libraries)using the requirements.txt file.
## How to Create a Python Virtual Environment

A **virtual environment** allows you to create isolated Python environments for different projects. This helps avoid dependency conflicts and keeps your workspace clean.



### Prerequisites

Make sure you have:

- **Python 3.6+** installed  
- `pip` installed (usually included with Python)

Check your versions:

```bash
python --version
pip --version
```

### Create a Virtual Environment
Use the built‑in venv module:

```bash 
python -m venv venv
```
This will create a folder named venv containing the isolated environment.

You can replace venv with any name:
```bash 
python -m venv venv
```
### Activate the Virtual Environment
Windows (PowerShell or CMD)
```bash
venv\Scripts\activate
```

macOS / Linux
```bash
source venv\bin\activate
```
When activated, your terminal prompt will show the environment name, e.g.:
```
(venv) $
```
### Install Packages Inside the Environment
Once activated, use pip normally to install the libraries in the requirements.txt file:
```bash
pip install -r requirements.txt
```
### Deactivate the Environment
To exit the virtual environment:
```bash
deactivate
```
---

## How to run the Python Scripts:
    -Open the project folder using an IDE (VScode, Pycharm or any Python IDE)
    -The .csv files containing the data to be analysed should be placed in the raw folder within the Scripts folder (./Scripts/raw).
    -Run the particular module inside the scripts folder.
    -The results will be exported to ./Scripts/processed.
    -The tests will run automatically when the each script finishes running.

The tests can also be run using the code:
```bash
pytest -q
```
Run a specific test file:
```bash
pytest ./tests/test_summary_statistics.py
```