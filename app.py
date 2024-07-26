import re

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import summaries
from app_helpers import (
    save_changes_to_file,
    copy_uploaded_file,
    save_summary_to_excel,
    CSV_EXTENSIONS,
    EXCEL_EXTENSIONS,
)


DELETE_REASON_COL = "delete_reason_column"

# variables shared between reruns
if "loaded_df" not in st.session_state:
    st.session_state.loaded_df = None
if "file_extension" not in st.session_state:
    st.session_state.file_extension = None
if "sheet_or_separator" not in st.session_state:
    st.session_state.sheet_or_separator = None
if "file_copy_path" not in st.session_state:
    st.session_state.file_copy_path = None

# background color
page_bg = """
        <style>
        [data-testid="stAppViewContainer"]{
            background-color: rgba(60, 91, 181, 1);
            background-image: linear-gradient(230deg, rgba(60, 91, 181, 1) 0%, rgba(41, 53, 86, 1) 100%);        }
        </style>
    """
st.markdown(page_bg, unsafe_allow_html=True)


def load_data(file_path, file_name):
    file_extension = file_name.split(".")[-1]
    if file_extension in CSV_EXTENSIONS:
        separator = st.selectbox(
            "Choose the separator",
            [",", ";", "\t", "|"],
            format_func=lambda x: "\\t" if x == "\t" else x,
        )
        if separator:
            loaded_df = pd.read_csv(file_path, sep=separator)
            if DELETE_REASON_COL not in loaded_df.columns:
                loaded_df[DELETE_REASON_COL] = ""
            return loaded_df, file_extension, separator
    elif file_extension in EXCEL_EXTENSIONS:
        excel_data = pd.ExcelFile(file_path)
        sheet_names = excel_data.sheet_names
        st.write("Excel File Loaded. Select a sheet to display:")
        sheet_name = st.selectbox("Select a sheet", sheet_names, index=None)
        if sheet_name:
            loaded_df = pd.read_excel(file_path, sheet_name=sheet_name)
            if DELETE_REASON_COL not in loaded_df.columns:
                loaded_df[DELETE_REASON_COL] = ""
            return loaded_df, file_extension, sheet_name
    return None, None, None


st.title("Audit Volkswagen")

uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file (to process a new file or new sheet reload page)", type=CSV_EXTENSIONS + EXCEL_EXTENSIONS
)

if uploaded_file is not None and st.session_state.loaded_df is None:
    file_name = uploaded_file.name
    st.session_state.file_copy_path, copy_file_exists = copy_uploaded_file(uploaded_file)
    # if copy_file_exists:
    #     st.write(f"Copy for this file was already created if you want to start new audit, delete it, path to the file: {st.session_state.file_copy_path}")
    (
        st.session_state.loaded_df,
        st.session_state.file_extension,
        st.session_state.sheet_or_separator,
    ) = load_data(st.session_state.file_copy_path, file_name)


# Start processing when data is loaded
if st.session_state.loaded_df is not None:
    loaded_df = st.session_state.loaded_df
    excluded_rows = len(loaded_df[loaded_df[DELETE_REASON_COL].str.len().ge(1)])
    df = loaded_df[~loaded_df[DELETE_REASON_COL].str.len().ge(1)].drop(
        columns=[DELETE_REASON_COL]
    )
    if st.session_state.file_extension in EXCEL_EXTENSIONS:
        st.header(
            f'Report for sheet "{st.session_state.sheet_or_separator}" from {uploaded_file.name} file'
        )
    elif st.session_state.file_extension in CSV_EXTENSIONS:
        st.header(f"Report for the file {uploaded_file.name}")
    else:
        st.write("Error, Unsupported file extension!")

    # ##############################################
    # Overall statistics
    # ##############################################   
    
    st.subheader("1. Dataset overall statistics")
    st.write(f"Dataset contains {df.shape[0]} rows and {df.shape[1]} columns.")
    st.write(f"In the dataset {excluded_rows} rows are excluded from analysis.")
    missing_values = df.isna().sum()
    st.write(f"{len(missing_values[missing_values > 0])} columns have missing values.")

    # Missing values visualization
    missing_values = missing_values.sort_values(ascending=True)

    fig, ax = plt.subplots()
    missing_values.plot(kind="barh")
    ax.set_title("Number of missing values form each column")
    ax.set_ylabel("Columns' names")
    ax.set_xlabel("Number of missing values")
    st.pyplot(fig)

    # ##############################################
    # ID columns
    # ############################################## 

    st.markdown("---")
    st.subheader("2. Columns with ID values")
    # Regular expression for finding ID columns
    id_pattern = r"(?i)(^|[\s_])id($|[\s_]|[a-zA-Z]*)"
    id_columns = [col for col in df.columns if re.search(id_pattern, col)]

    id_columns_to_show = st.multiselect(
        "Select ID columns. By default only first 5 columns are selected.",
        options=df.columns.tolist(),
        default=id_columns[:5],
    )

    all_id_results = []

    for id_col in id_columns:
        results, duplicated_ids = summaries.prepare_id_column_info(df, id_col)
        results["col_name"] = id_col
        all_id_results.append(results)
        output = summaries.id_column_summary(results, id_col)
        if id_col in id_columns_to_show:
            st.markdown(output)
            if len(duplicated_ids) > 0:
                st.dataframe(duplicated_ids)
    save_summary_to_excel(
        all_id_results, uploaded_file, sheet_name="ID columns", mode="w"
    )

    # ##############################################
    # Date columns
    # ############################################## 

    st.markdown("---")
    st.subheader("3. Columns with Date Values")

    date_columns = df.select_dtypes(include=["datetime64"]).columns.tolist()

    # try to load columns from date_columns as dates
    to_remove = []
    for col in date_columns:
        try:
            df[col] = pd.to_datetime(df[col])
        except pd._libs.tslibs.parsing.DateParseError:
            st.write(
                f"Error during parsing {col} column. It will be excluded from date columns"
            )
            to_remove.append(col)

    date_columns = [col for col in date_columns if col not in to_remove]

    date_columns_to_show = st.multiselect(
        "Select columns with date values. By default only first 5 columns are selected.",
        options=df.columns.tolist(),
        default=date_columns[:5],
    )

    all_date_results = []

    for date_col in date_columns:
        results, outliers = summaries.prepare_date_column_info(df, date_col)
        results["col_name"] = date_col
        output = summaries.date_column_summary(results, date_col)
        if date_col in date_columns_to_show:
            st.markdown(output)
            if len(outliers) > 0:
                st.dataframe(outliers)
        all_date_results.append(results)

    save_summary_to_excel(
        all_date_results, uploaded_file, sheet_name="date columns", mode="a"
    )

    st.subheader("3.1 Date Distribution Plots")

    date_columns_to_plot = st.multiselect(
        "Select columns with date values to plot their distribution. By default only first 5 columns are selected.",
        options=date_columns,
        default=date_columns[:5],
    )
    for date_col in date_columns_to_plot:
        # Visualization - Date distribution
        fig, ax = plt.subplots()
        sns.histplot(df[date_col].dropna(), bins=30, kde=True, ax=ax)
        ax.set_title(f"Dates Distribution for the column {date_col}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of examples")
        ax.tick_params(axis="x", labelrotation=45)
        st.pyplot(fig)

    st.subheader("3.2 Exclude rows form the report")

    if date_columns:
        st.write(
            "In this section you can exclude rows which contain date values which are before, after or between a chosen dates."
        )
        date_column = st.selectbox("Select date column", date_columns)
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("After", value=None, key="start_date")
        with col2:
            end_date = st.date_input("Before", value=None, key="end_date")
        reason = st.text_input(
            "Enter additional info why date rows are excluded from the report."
        )

        if st.button("Exclude rows from the report", key="Exclude button date"):
            if reason:
                condition = pd.Series([True] * len(loaded_df))
                if start_date:
                    condition &= loaded_df[date_column] >= pd.to_datetime(start_date)
                if end_date:
                    condition &= loaded_df[date_column] <= pd.to_datetime(end_date)

                reason_message = f"Rows in column {date_column} with condition 'between {start_date} and {end_date}' have been marked for excluding with reason: {reason}"
                loaded_df.loc[condition, DELETE_REASON_COL] = reason_message
                st.session_state.loaded_df = loaded_df
                st.write(
                    f"{sum(condition)} rows were excluded from the report, reason was saved into copy of the original file."
                )
                save_changes_to_file(
                    loaded_df,
                    st.session_state.file_copy_path,
                    st.session_state.file_extension,
                    st.session_state.sheet_or_separator,
                )
            else:
                st.write("Please select values and enter a reason to mark rows.")
    else:
        st.write("No date columns available.")

    if st.button("Rerun Report", key="Rerun button date"):
        st.rerun()

    # ##############################################
    # Numeric columns
    # ############################################## 

    st.markdown("---")
    st.subheader("4. Columns with Numeric Values")

    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_columns = [col for col in numeric_columns if col not in id_columns]

    numeric_columns_to_show = st.multiselect(
        "Select columns with numeric values. By default only first 5 columns are selected.",
        options=df.columns.tolist(),
        default=numeric_columns[:5],
    )

    all_numeric_results = []

    for numeric_col in numeric_columns:
        results, outliers = summaries.prepare_numeric_column_info(df, numeric_col)
        results["col_name"] = numeric_col
        output = summaries.numeric_column_summary(results, numeric_col)
        if numeric_col in numeric_columns_to_show:
            st.markdown(output)
            if len(outliers) > 0:
                st.dataframe(outliers)

        all_numeric_results.append(results)

    save_summary_to_excel(
        all_numeric_results, uploaded_file, sheet_name="numeric columns", mode="a"
    )

    st.subheader("4.1 Numeric Data Distribution and Correlation Plots")

    numeric_columns_to_plot = st.multiselect(
        "Select columns with numeric values to plot their distribution and correlation. By default only first 5 columns are selected.",
        options=numeric_columns,
        default=numeric_columns[:5],
    )

    fig = sns.pairplot(df[numeric_columns_to_plot].dropna())
    st.pyplot(fig)

    correlation_matrix = df[numeric_columns_to_plot].corr()
    fig, ax = plt.subplots()
    sns.heatmap(
        correlation_matrix,
        vmin=-1,
        vmax=1,
        annot=True,
        cmap="coolwarm",
        linewidths=0.5,
        ax=ax,
    )
    ax.tick_params(axis="y", labelrotation=90)
    ax.set_title("Correlation matrix")
    st.pyplot(fig)

    st.subheader("4.2 Exclude rows form the report")

    if numeric_columns:
        st.write(
            "In this section you can exclude rows which contain numeric value which are greater or smaller than chosen threshold."
        )
        num_column = st.selectbox("Select numeric column", numeric_columns)
        min_value, max_value = float(loaded_df[num_column].min()), float(
            loaded_df[num_column].max()
        )
        selected_range = st.slider(
            "Select range", min_value, max_value, (min_value, max_value)
        )

        reason = st.text_input(
            "Enter additional info why numeric rows are excluded from the report."
        )

        if st.button("Exclude rows from the report", key="Exclude button numeric"):
            if reason:
                condition = (loaded_df[num_column] >= selected_range[0]) & (
                    loaded_df[num_column] <= selected_range[1]
                )
                reason_message = f"Rows in column {num_column} with values in range '{selected_range[0]}, {selected_range[1]}' have been marked for excluding with reason: {reason}"
                loaded_df.loc[condition, DELETE_REASON_COL] = reason_message
                st.session_state.loaded_df = loaded_df
                save_changes_to_file(
                    loaded_df,
                    st.session_state.file_copy_path,
                    st.session_state.file_extension,
                    st.session_state.sheet_or_separator,
                )
                st.write(
                    f"{sum(condition)} rows were excluded from the report, reason was saved into copy of the original file."
                )
            else:
                st.write("Please select values and enter a reason to mark rows.")
    else:
        st.write("No numeric columns available.")

    if st.button("Rerun Report", key="Rerun button numeric"):
        st.rerun()

    # ##############################################
    # Text columns
    # ############################################## 

    st.markdown("---")
    st.subheader("5. Columns with Text Values")

    text_columns = [
        col
        for col in df.columns
        if col not in id_columns + numeric_columns + date_columns
    ]
    threshold = 10

    text_columns_to_show = st.multiselect(
        "Select columns with text values to summary their distribution. By default only first 5 columns are selected.",
        options=text_columns,
        default=text_columns[:5],
    )

    all_text_results = []

    for text_col in text_columns:
        results = summaries.prepare_text_column_info(df, text_col)
        results["col_name"] = text_col
        output = summaries.text_column_summary(results, text_col)
        if text_col in text_columns_to_show:
            st.markdown(output)
        all_text_results.append(results)

    save_summary_to_excel(
        all_text_results, uploaded_file, sheet_name="text columns", mode="a"
    )

    categorical_cols = [col for col in text_columns if df[col].nunique() <= threshold]
    text_cols = [col for col in text_columns if col not in categorical_cols]

    st.subheader("5.1 Data Distribution Plots for Categorical Values")

    cat_columns_to_plot = st.multiselect(
        "Select columns with categorical values to plot their distribution. By default only first 5 columns are selected.",
        options=categorical_cols,
        default=categorical_cols[:5],
    )

    for cat_col in cat_columns_to_plot:
        fig, ax = plt.subplots(layout="tight")
        value_counts = df[cat_col].value_counts(dropna=False)
        # If there are missing values, replace index name with meaningful name
        if any(value_counts.index.isna()):
            nan_count = value_counts.loc[np.nan]
            value_counts = value_counts[value_counts.index.notnull()]
            value_counts["Missing values"] = nan_count
        sns.barplot(
            x=value_counts.values, y=value_counts.index, palette="viridis", ax=ax
        )
        ax.set_title(f"Category Distribution from {cat_col} column")
        ax.set_xlabel("Number of examples")
        ax.set_ylabel(cat_col)

        for i in range(len(value_counts)):
            ax.text(
                value_counts[i],
                i,
                str(value_counts.values[i]),
                color="black",
                ha="left",
                va="center",
            )
        st.pyplot(fig)

    st.subheader("Exclude rows from the report")

    st.write(
        "In this section you can exclude rows which contain given value in the chosen column."
    )

    column = st.selectbox("Select column", df.columns)
    values = st.multiselect("Select values to mark for deletion", df[column].unique())
    reason = st.text_input("Enter the reason for marking rows for deletion")

    if st.button("Exclude rows from the report", key="Exclude button all"):
        if values and reason:
            reason_message = f"Rows with values {values} in column {column} have been marked for deletion with reason: {reason}"
            loaded_df.loc[loaded_df[column].isin(values), DELETE_REASON_COL] = (
                reason_message
            )
            st.session_state.loaded_df = loaded_df
            save_changes_to_file(
                loaded_df,
                st.session_state.file_copy_path,
                st.session_state.file_extension,
                st.session_state.sheet_or_separator,
            )
            st.write(
                f"{sum(loaded_df[column].isin(values))} rows were excluded from the report, reason was saved into copy of the original file."
            )
        else:
            st.write("Please select values and enter a reason to mark rows.")

    if st.button("Rerun Report", key="Rerun button all"):
        st.rerun()
