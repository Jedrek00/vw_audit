from typing import Tuple
import numpy as np
import pandas as pd


def prepare_id_column_info(df: pd.DataFrame, column: str) -> Tuple[dict, pd.Series]:
    """
    Analyze and summarize information about an ID column in a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the ID column.
    column (str): The name of the ID column to analyze.

    Returns:
    dict: A dictionary containing the following information:
        - "missing_values" (int): The number of missing (null) values in the ID column.
        - "duplicated_values_count" (int): The count of unique duplicated values in the ID column.
        - "lengths" (dict): A dictionary where keys are the lengths of the ID values and values are their counts.
        - "is_numeric" (bool): Whether all values in the ID column are numeric.
        - "is_alphanumeric" (bool): Whether all values in the ID column are alphanumeric.
    """
    results = {}
    results["missing_values"] = df[column].isnull().sum()
    vc = df[column].value_counts()
    duplicated_values = vc[vc > 1]
    results["duplicated_values_count"] = len(vc[vc > 1])
    lengths = {}
    id_lengths = df[column].astype(str).apply(len)
    id_lengths_counts = id_lengths.value_counts()
    for length, count in id_lengths_counts.items():
        lengths[length] = count
    results["lengths"] = lengths
    results["is_numeric"] = df[column].astype(str).str.isnumeric().all()
    results["is_alphanumeric"] = df[column].astype(str).str.isalnum().all()
    return results, duplicated_values


def id_column_summary(results: dict, column_name: str) -> str:
    """
    Generate a summary report for an ID column based on analyzed results.

    Parameters:
    results (dict): A dictionary containing the analysis results of the ID column.
    column_name (str): The name of the ID column being summarized.

    Returns:
    str: A formatted string summarizing the analysis results for the specified ID column.
    """
    output = f"\nResults for **{column_name}**:"

    output += f"\n* Number of the missing values: {results['missing_values']}"

    output += "\n* Length of the ID and number of occurences:"
    for length, count in results["lengths"].items():
        output += f"\n\t* Length {length}: {count}"

    output += f"\n* It has only numeric values: {results['is_numeric']}"
    output += f"\n* It has only alpha-numeric values: {results['is_alphanumeric']}"

    output += f"\n* Number of duplicated IDs: {results['duplicated_values_count']}"

    return output


def prepare_date_column_info(df: pd.DataFrame, column: str) -> Tuple[dict, pd.Series]:
    """
    Analyze and summarize information about a date column in a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the date column.
    column (str): The name of the date column to analyze.

    Returns:
    tuple: A tuple containing two elements:
        - dict: A dictionary with the following keys:
            - "missing_values" (int): The number of missing (null) values in the date column.
            - "min_date" (pd.Timestamp): The minimum date in the column.
            - "max_date" (pd.Timestamp): The maximum date in the column.
            - "mean_date" (pd.Timestamp): The mean (average) date in the column.
            - "median_date" (pd.Timestamp): The median date in the column.
            - "mode_date" (pd.Timestamp or np.nan): The mode (most frequent) date in the column, or NaN if no mode exists.
            - "outliers_count" (int): The number of outliers detected in the date column.
        - pd.Series: A Series of the outlier dates in the date column.
    """
    results = {}
    results["missing_values"] = df[column].isnull().sum()
    # dates statistics
    results["min_date"] = df[column].min()
    results["max_date"] = df[column].max()
    results["mean_date"] = df[column].mean()
    results["median_date"] = df[column].median()
    results["mode_date"] = (
        df[column].mode().iloc[0] if not df[column].mode().empty else np.nan
    )

    # Detecting outliers (using IQR method for demonstration)
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)][column]

    results["outliers_count"] = len(outliers)

    return results, outliers


def date_column_summary(results: dict, column_name: str) -> str:
    """
    Generate a summary report for a date column based on analyzed results.

    Parameters:
    results (dict): A dictionary containing the analysis results of the date column.
    column_name (str): The name of the date column being summarized.

    Returns:
    str: A formatted string summarizing the analysis results for the specified date column.
    """
    output = f"\nResults for **{column_name}**:"
    output += f"\n* Dates are from {results['min_date']} to {results['max_date']}"
    output += f"\n* Number of the missing values: {results['missing_values']}"
    # Statistics about dates
    output += "\n* Statistics: "
    output += f"\n\t* mean: {results['mean_date']}"
    output += f"\n\t* median: {results['median_date']}"
    output += f"\n\t* mode: {results['mode_date']}"
    output += f"\n* Number of potential outliers: {results['outliers_count']}"

    return output


def prepare_numeric_column_info(
    df: pd.DataFrame, column: str
) -> Tuple[dict, pd.Series]:
    """
    Analyze and summarize information about a numeric column in a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the numeric column.
    column (str): The name of the numeric column to analyze.

    Returns:
    tuple: A tuple containing two elements:
        - dict: A dictionary with the following keys:
            - "min_value" (float): The minimum value in the column.
            - "max_value" (float): The maximum value in the column.
            - "mean_value" (float): The mean (average) value in the column.
            - "median_value" (float): The median value in the column.
            - "std_dev" (float): The standard deviation of the values in the column.
            - "missing_values" (int): The number of missing (null) values in the column.
            - "outliers_count" (int): The number of outliers detected in the column based on the IQR method.
        - pd.Series: A Series of the outlier values in the column.
    """
    results = {}

    results["min_value"] = df[column].min()
    results["max_value"] = df[column].max()
    results["mean_value"] = df[column].mean()
    results["median_value"] = df[column].median()
    results["std_dev"] = df[column].std()
    results["missing_values"] = df[column].isnull().sum()

    # Outlier detection using IQR method
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)][column]

    results["outliers_count"] = len(outliers)

    return results, outliers


def numeric_column_summary(results, column: str) -> str:
    """
    Generate a summary report for a numeric column based on analyzed results.

    Parameters:
    results (dict): A dictionary containing the analysis results of the numeric column.
    column (str): The name of the numeric column being summarized.

    Returns:
    str: A formatted string summarizing the analysis results for the specified numeric column.
    """
    output = f"\nResults for **{column}**:"

    output += f"\n* Number of the missing values: {results['missing_values']}"

    output += "\n* Statistics: "
    output += f"\n\t* min: {results['min_value']:.2f}"
    output += f"\n\t* max: {results['max_value']:.2f}"
    output += f"\n\t* mean: {results['mean_value']:.2f}"
    output += f"\n\t* median: {results['median_value']:.2f}"
    output += f"\n\t* std: {results['std_dev']:.2f}"
    output += f"\n\t* mean: {results['missing_values']:.2f}"

    output += f"\n* Number of potential outliers: {results['outliers_count']}"
    return output


def prepare_text_column_info(df: pd.DataFrame, column: str) -> dict:
    """
    Analyze and summarize information about a text column in a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing the text column.
    column (str): The name of the text column to analyze.

    Returns:
    dict: A dictionary with the following keys:
        - "missing_values" (int): The number of missing (null) values in the text column.
        - "unique_values" (int): The number of unique values in the text column.
        - "most_popular_value" (str, optional): The most frequently occurring value in the text column, if there are no missing values.
        - "number_of_occ" (int, optional): The count of occurrences of the most popular value, if there are no missing values.
    """
    results = {}
    results["missing_values"] = df[column].isnull().sum()
    results["unique_values"] = df[column].nunique()
    if results["missing_values"] < len(df[column]):
        results["most_popular_value"] = df[column].mode()[0]
        results["number_of_occ"] = df[column].value_counts().iloc[0]
    return results


def text_column_summary(results, column: str) -> str:
    """
    Generate a summary report for a text column based on analyzed results.

    Parameters:
    results (dict): A dictionary containing the analysis results of the text column.
    column (str): The name of the text column being summarized.

    Returns:
    str: A formatted string summarizing the analysis results for the specified text column.
    """
    output = f"\nResults for **{column}**:"
    output += f"\n* Number of the missing values: {results['missing_values']}"
    output += f"\n* Number of unique values: {results['unique_values']}"
    if "most_popular_value" in results:
        output += f"\n* Most popular value: {results['most_popular_value']}"
        output += f"\n* Number of occurrence of the most popular value: {results['number_of_occ']}"

    return output
