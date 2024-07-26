import shutil
from pathlib import Path
from typing import Tuple

import pandas as pd

# Change this path if you want to save results of the audit in different location
AUDIT_DIR_PATH = Path("audit_files")

# If you want to process other file types, add extension to those lists,
# extensions have to be supported by the pandas and streamlit.file_uploader
CSV_EXTENSIONS = ["csv"]
EXCEL_EXTENSIONS = ["xlsx"]


def save_summary_to_excel(
    results: dict, uploaded_file, sheet_name: str, mode: str
) -> None:
    """
    Save the results dictionary to an Excel file.

    Parameters:
    results (dict): The results dictionary to save.
    filename (str): The name of the Excel file.
    sheet_name (str): The name of the sheet in the Excel file.
    """
    results_df = pd.DataFrame.from_dict(results)

    original_name = uploaded_file.name
    original_stem = Path(original_name).stem
    summary_file_name = f"{original_stem}_summary.xlsx"

    with pd.ExcelWriter(
        AUDIT_DIR_PATH.joinpath(summary_file_name), mode=mode
    ) as writer:
        results_df.to_excel(writer, sheet_name=sheet_name, index=False)


def copy_uploaded_file(uploaded_file) -> Tuple[str, bool]:
    """
    Copy an uploaded file to a new location with an "_audit" suffix in the filename.

    Parameters:
    uploaded_file: A file-like object representing the uploaded file.

    Returns:
    str: The path to the newly created file with the "_audit" suffix.
    """
    original_name = uploaded_file.name
    original_stem = Path(original_name).stem
    file_extension = Path(original_name).suffix

    # Create the new file name with the "_audit" suffix
    copied_file_name = f"{original_stem}_audit{file_extension}"
    copy_path = AUDIT_DIR_PATH / copied_file_name

    # Ensure the directory exists
    copy_path.parent.mkdir(parents=True, exist_ok=True)

    copy_file_exists = copy_path.exists()

    # Copy the uploaded file to the new location
    if not copy_file_exists:
        with copy_path.open("wb") as copy_file:
            shutil.copyfileobj(uploaded_file, copy_file)

    return str(copy_path), copy_file_exists


def save_changes_to_file(
    df: pd.DataFrame, path: str, extension: str, sep_or_sheet: str
):
    """
    Save a DataFrame to a file in CSV or Excel format.

    Parameters:
    df (pd.DataFrame): The DataFrame to be saved.
    path (str): The file path where the DataFrame will be saved.
    extension (str): The file extension indicating the format. Should be 'csv' or 'xlsx'.
    sep_or_sheet (str):
        - For 'csv': The separator to use when writing the CSV file (e.g., ',' or ';').
        - For 'xlsx': The name of the sheet in the Excel file to write the DataFrame to.

    Notes:
    - For CSV files, the `sep_or_sheet` parameter is used as the separator in the CSV file.
    - For Excel files, the `sep_or_sheet` parameter is used as the sheet name in the Excel workbook.
      If a sheet with this name already exists, it will be removed before writing the DataFrame.
    """
    if extension in CSV_EXTENSIONS:
        separator = sep_or_sheet
        df.to_csv(path, sep=separator, index=False)
    elif extension in EXCEL_EXTENSIONS:
        with pd.ExcelWriter(path, engine="openpyxl", mode="a") as writer:
            # Remove the sheet if it already exists to avoid errors
            sheet_name = sep_or_sheet
            if sheet_name in writer.book.sheetnames:
                idx = writer.book.sheetnames.index(sheet_name)
                writer.book.remove(writer.book.worksheets[idx])
            # Write the DataFrame to the specified sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        print("Unsupported extension of the file!")
