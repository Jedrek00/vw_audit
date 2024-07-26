# Audit Application

## Overview

This Streamlit application is designed for performing audits on data files with extensions .xlsx and .csv. It processes each sheet independently, without requiring specific column names, making it flexible and adaptable to various data structures. The application categorizes columns into four groups: IDs, Dates, Numeric, and Text. Each group has its own summary, which includes plots, statistics, and options to exclude elements based on their values. The original file remains unmodified during processing. All changes are saved in a copy of the original file, and summary files for each sheet are saved in the specified location. 

You can specified which rows should be marked as potential errors using this app, information about selected rows will be saved in the additional column in the copy of the original file. Rows selected as errors will be excluded from the analysis. Information how many rows were excluded are at the top of the app in section *Overall statistics*. Additionally statistics showed in the app are saved in the *\*_summary.xlsx* file, storing information for each type of the columns. By default copy of the original file with information about excluded file and summary file will be saved in the same directory as this project. You can change path by modifying `AUDIT_DIR_PATH` in `app_helpers.py`.

To change maximum size limit of the processed file modify value in the `.streamlit/config.toml`.

## Installation

Prerequisites: Python 3.7 or later

1. Unzip project and change directory to the project dir

```bash
cd vw_audit
```

2. [Optional] Create a [Virtual Environment](https://docs.python.org/3/tutorial/venv.html) to have a separate Python space
* On Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```
* On Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required libraries
```bash
pip install -r requirements.txt
```

## Usage

1. Launch the application by running 
```
streamlit run app.py
```
2. Upload your .xlsx or .csv file.
3. The application will process selected sheet in the file and categorize the columns into IDs, Dates, Numeric, and Text.
4. For each group, the application will provide summaries including plots and statistics.
5. You can exclude elements based on their values during the review.
6. All modifications and summaries will be saved to a copy of the original file at the path specified in `app_helpers.py`.

## Streamlit

[Streamlit](https://docs.streamlit.io/) is an open-source app framework for Machine Learning and Data Science projects. It allows you to create web applications for your data analysis with minimal code. You write a script using Streamlit's API to define the app's components, such as text, data displays, charts, and interactive widgets. When you run the script, Streamlit generates a web app that opens in a browser. The app updates in real-time as the script changes. When users interact with the app, such as moving a slider or clicking a button, Streamlit reruns the script from top to bottom with the new input values, providing immediate feedback and dynamic updates

## Author

Jędrzej Kościelniak for the "Be the Best" 2024 contest
