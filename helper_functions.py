import atexit
import logging
import sqlite3
import traceback
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st

# Configure logging
logging.basicConfig(
    filename="./logs/app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def download_pdf(filepath):
    try:
        # Read the file content
        with open(filepath, "rb") as file:
            pdf_bytes = file.read()

        # Display the download button
        st.download_button(
            "Download Guideline PDF",
            data=pdf_bytes,
            file_name="Sunlife_Annotation_Tool_Guidelines.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        # Log the error message and traceback
        logging.error("An error occurred while downloading the PDF file:")
        logging.error(traceback.format_exc())


# Register a function to close the database connection.
def close_database(cursor, connection):
    # Close the database connection.
    try:
        cursor.close()
        connection.close()
        logging.info(f"Connection to the database closed.")

    # it is closing multiple instances of connections...
    # so from the second time onwards
    # it throws error, hence we are catching that exception
    # and just passing it!
    except sqlite3.ProgrammingError:
        # print("exception caught!!")
        pass

    except Exception as e:
        logging.error(
            "An unexpected error occurred while closing connection to the database."
        )
        logging.error(traceback.format_exc())
        raise


@st.cache_resource
def init_connection() -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """
    Initialize connection to the SQLite database.

    Returns:
        conn (sqlite3.Connection): Connection object to the database.
        cursor (sqlite3.Cursor): Cursor object for executing SQL queries.
    """
    try:
        # Connect to the database (creates a new database if it doesn't exist)
        conn = sqlite3.connect("./outputs/annotations_db.db", check_same_thread=False)
        cursor = conn.cursor()

        logging.info(
            f"Connection to the database initialized. User: {st.session_state.get('name')}"
        )
        return conn, cursor

    except sqlite3.Error as e:
        logging.error("Failed to initialize connection to the database.")
        logging.error(traceback.format_exc())
        raise

    except Exception as e:
        logging.error(
            "An unexpected error occurred while initializing connection to the database."
        )
        logging.error(traceback.format_exc())
        raise


@st.cache_data
def get_unannotated_ids(
    call_data: pd.DataFrame,
    annotated_df: pd.DataFrame,
    user_call_mapping: pd.DataFrame,
    username: str,
) -> pd.DataFrame:
    """
    Get the unannotated IDs based on the call data, annotated dataframe, user-call mapping, and username.

    Args:
        call_data (pd.DataFrame): DataFrame containing call data.
        annotated_df (pd.DataFrame): DataFrame containing annotated data.
        user_call_mapping (pd.DataFrame): DataFrame containing user-call mapping.
        username (str): Username of the annotator.

    Returns:
        pd.DataFrame: DataFrame containing the unannotated IDs.
    """
    try:
        call_ids = (
            pd.merge(call_data, user_call_mapping, on="ConnectionID", how="left")
            .query("Annotator == @username")
            .assign(
                new_id=lambda x: x["ConnectionID"]
                + "_chunk_"
                + x["chunk_id"].astype(str)
            )
            .sort_values(by=["ConnectionID", "chunk_id"])
            .reset_index(drop=True)
        )

        # Perform outer join
        outer = call_ids.merge(
            annotated_df,
            left_on="new_id",
            right_on="call_id",
            how="outer",
            indicator=True,
        )

        # Perform anti-join
        anti_join = outer[(outer._merge == "left_only")].drop("_merge", axis=1)

        return anti_join

    except Exception as e:
        logging.error("An error occurred while retrieving unannotated IDs.")
        logging.error(traceback.format_exc())
        raise


@st.cache_data
def read_dataframes() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Read the dataframes from parquet files.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: A tuple containing the dataframes (data, intents, mapping).
    """
    try:
        data = pd.read_parquet("./inputs/data.parquet")
        intents = pd.read_parquet("./inputs/intents.parquet")
        mapping = pd.read_parquet("./inputs/mapping.parquet")

        return data, intents, mapping

    except Exception as e:
        logging.error("An error occurred while reading the dataframes.")
        logging.error(traceback.format_exc())
        raise


@st.cache_data
def read_annotated_data(_conn) -> pd.DataFrame:
    """
    Read the annotated data from the call_annotation_table in the database.

    Args:
        _conn: The database connection object.

    Returns:
        pd.DataFrame: The dataframe containing the annotated data.
    """
    try:
        select_data_query = "SELECT * FROM call_annotation_table"
        df = pd.read_sql_query(select_data_query, _conn)

        return df

    except Exception as e:
        logging.error("An error occurred while reading the annotated data.")
        logging.error(traceback.format_exc())
        raise


@st.cache_data
def get_all_intent_options(intent_df: pd.DataFrame) -> List[str]:
    """
    Get all unique intent options from the intent dataframe.

    Args:
        intent_df (pd.DataFrame): The dataframe containing the intent data.

    Returns:
        List[str]: A list of all unique intent options.
    """
    try:
        all_intents = intent_df["Intent"].unique().tolist()
        return all_intents

    except Exception as e:
        logging.error("An error occurred while getting all intent options.")
        logging.error(traceback.format_exc())
        raise


@st.cache_data
def get_all_subintent_options(intent_df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Get all subintent options for each intent from the intent dataframe.

    Args:
        intent_df (pd.DataFrame): The dataframe containing the intent data.

    Returns:
        Dict[str, List[str]]: A dictionary mapping each intent to a list of its subintent options.
    """
    try:
        si_map = intent_df.groupby("Intent")["Sub Intent"].unique().to_dict()
        sub_intent_map = {k: list(v) for k, v in si_map.items()}
        return sub_intent_map

    except Exception as e:
        logging.error("An error occurred while getting all subintent options.")
        logging.error(traceback.format_exc())
        raise


def get_valid_subintent_options(
    intent_list: List[str], subintent_map: Dict[str, List[str]]
) -> List[str]:
    """
    Get valid sub-intent options for a given list of intents from the sub-intent map.

    Args:
        intent_list (List[str]): The list of intents.
        subintent_map (Dict[str, List[str]]): The sub-intent map.

    Returns:
        List[str]: The list of valid sub-intent options.
    """
    try:
        sub_intent_list = []
        for intent in intent_list:
            sub_intent_list.extend(subintent_map.get(intent, []))

        return sub_intent_list
    except Exception as e:
        logging.error(f"An error occurred in 'get_valid_subintent_options': {e}")
        logging.error(traceback.format_exc())
        raise


def save_data_to_table(
    conn,
    cursor,
    new_id,
    user,
    role,
    current_date,
    current_time,
    sel_int_str,
    sel_subint_str,
    confidence,
    comment,
):
    """
    Save data to the database table.

    Args:
        conn: The database connection object.
        cursor: The cursor object to execute SQL queries.
        new_id (str): The new ID value.
        user (str): The username.
        role (str): The role.
        current_date (str): The current date.
        current_time (str): The current time.
        sel_int_str (str): The selected intent value.
        sel_subint_str (str): The selected sub-intent value.
        confidence (float): The confidence value.
        comment (str): The comment.

    Returns:
        None
    """
    try:
        # Insert values into the table using parameterized query
        query = (
            "INSERT INTO call_annotation_table (call_id, username, role, date, time, case_type, subcase_type, confidence, comments) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        values = (
            new_id,
            user,
            role,
            current_date,
            current_time,
            sel_int_str,
            sel_subint_str,
            confidence,
            comment,
        )
        cursor.execute(query, values)

        # Commit the changes to the database
        conn.commit()

    except Exception as e:
        logging.error(f"An error occurred in 'save_data_to_table': {e}")
        logging.error(traceback.format_exc())


def previous_button_clicked_reviewer():
    """
    Handle the click event of the previous button for the reviewer.

    Returns:
        None
    """
    try:
        idx = st.session_state["current_idx"] - 1

        if idx == -1:
            idx = st.session_state["n_chunks"] - 1

        st.session_state["current_idx"] = idx

    except Exception as e:
        logging.error(f"An error occurred in 'previous_button_clicked_reviewer': {e}")
        logging.error(traceback.format_exc())


def next_button_clicked_reviewer():
    """
    Handle the click event of the next button for the reviewer.

    Returns:
        None
    """
    try:
        idx = st.session_state["current_idx"] + 1

        if idx == st.session_state["n_chunks"]:
            idx = 0

        st.session_state["current_idx"] = idx

    except Exception as e:
        logging.error(f"An error occurred in 'next_button_clicked_reviewer': {e}")
        logging.error(traceback.format_exc())


def save_next_button_clicked_reviewer(
    conn, cursor, new_id, selected_intents, selected_subintents, confidence, comment
):
    """
    Handle the click event of the save and next button for the reviewer.

    Args:
        conn (sqlite3.Connection): SQLite database connection object.
        cursor (sqlite3.Cursor): SQLite database cursor object.
        new_id (str): New ID value.
        selected_intents (list): List of selected intents.
        selected_subintents (list): List of selected subintents.
        confidence (float): Confidence value.
        comment (str): Comment value.

    Returns:
        None
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        sel_int_str = ", ".join(selected_intents)
        sel_subint_str = ", ".join(selected_subintents)

        user = st.session_state.get("name")
        role = st.session_state.get("role")

        save_data_to_table(
            conn,
            cursor,
            new_id,
            user,
            role,
            current_date,
            current_time,
            sel_int_str,
            sel_subint_str,
            confidence,
            comment,
        )

        idx = st.session_state["current_idx"] + 1

        if idx == st.session_state["n_chunks"]:
            idx = 0

        st.session_state["current_idx"] = idx

    except Exception as e:
        logging.error(f"An error occurred in 'save_next_button_clicked_reviewer': {e}")
        logging.error(traceback.format_exc())


def previous_button_clicked():
    """
    Handle the click event of the previous button for annotator.

    Returns:
        None
    """
    try:
        idx = st.session_state["current_idx"] - 1

        while True:
            if idx == -1:
                idx = st.session_state["n_chunks"] - 1
            if idx not in st.session_state["annotated_idx"]:
                st.session_state["current_idx"] = idx
                break
            idx -= 1
    except Exception as e:
        logging.error(f"An error occurred in 'previous_button_clicked': {e}")
        logging.error(traceback.format_exc())


def next_button_clicked():
    """
    Handle the click event of the next button.

    Returns:
        None
    """
    try:
        idx = st.session_state["current_idx"] + 1

        while True:
            if idx == st.session_state["n_chunks"]:
                idx = 0
            if idx not in st.session_state["annotated_idx"]:
                st.session_state["current_idx"] = idx
                break
            idx += 1
    except Exception as e:
        logging.error(f"An error occurred in 'next_button_clicked': {e}")
        logging.error(traceback.format_exc())


def save_next_button_clicked(
    conn, cursor, new_id, selected_intents, selected_subintents, confidence, comment
):
    """
    Handle the click event of the save next button.

    Args:
        conn (sqlite3.Connection): The SQLite database connection.
        cursor (sqlite3.Cursor): The SQLite cursor.
        new_id (str): The new ID for the annotation.
        selected_intents (list): The selected intents.
        selected_subintents (list): The selected subintents.
        confidence (float): The confidence score.
        comment (str): The comment.

    Returns:
        None
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        sel_int_str = ", ".join(selected_intents)
        sel_subint_str = ", ".join(selected_subintents)

        user = st.session_state.get("name")
        role = st.session_state.get("role")

        save_data_to_table(
            conn,
            cursor,
            new_id,
            user,
            role,
            current_date,
            current_time,
            sel_int_str,
            sel_subint_str,
            confidence,
            comment,
        )

        st.session_state["annotated_idx"].add(st.session_state["current_idx"])

        if len(st.session_state["annotated_idx"]) == st.session_state["n_chunks"]:
            st.session_state["all_done"] = True
            return

        idx = st.session_state["current_idx"] + 1

        while True:
            if idx == st.session_state["n_chunks"]:
                idx = 0

            if idx not in st.session_state["annotated_idx"]:
                st.session_state["current_idx"] = idx
                break
            idx += 1
    except Exception as e:
        logging.error(f"An error occurred in 'save_next_button_clicked': {e}")
        logging.error(traceback.format_exc())


def get_default_options(values):
    """
    Get the list of options from a comma-separated string.

    Args:
        values (str): Comma-separated values.

    Returns:
        list: The default options.
    """
    try:
        if values is None or values == "":
            return []

        options = [s.strip() for s in values.split(",")]
        return options
    except Exception as e:
        logging.error(f"An error occurred in 'get_default_options': {e}")
        logging.error(traceback.format_exc())


def get_call_ids_to_be_reviewed(
    call_data: pd.DataFrame,
    user_call_mapping: pd.DataFrame,
    annot_data: pd.DataFrame,
    rev_username: str,
) -> pd.DataFrame:
    """
    Retrieve the call IDs to be reviewed based on the given input data.

    Args:
        call_data (pd.DataFrame): Dataframe containing call information.
        user_call_mapping (pd.DataFrame): Dataframe containing user-call mapping information.
        annot_data (pd.DataFrame): Dataframe containing annotation data.
        rev_username (str): Username of the reviewer.

    Returns:
        pd.DataFrame: Dataframe containing the call IDs to be reviewed.

    Raises:
        Exception: If an error occurs while retrieving call IDs to be reviewed.
    """

    try:
        only_annotator_data = annot_data.query("role == 'annotator'")

        call_ids = (
            pd.merge(call_data, user_call_mapping, on="ConnectionID", how="left")
            .query("Reviewer == @rev_username")
            .assign(
                new_id=lambda x: x["ConnectionID"]
                + "_chunk_"
                + x["chunk_id"].astype(str)
            )
            .merge(
                only_annotator_data,
                left_on=["new_id"],
                right_on=["call_id"],
                how="inner",
            )
            .sort_values(by=["ConnectionID", "chunk_id"])
            .reset_index(drop=True)
        )

        return call_ids

    except Exception as e:
        logging.error("An error occurred while retrieving call IDs to be reviewed.")
        logging.error(traceback.format_exc())
        raise e


def get_already_reviewed_calls(_conn, connection_id, chunk_id):
    """
    Get the status and review data for a specific call chunk.

    Args:
        _conn (sqlite3.Connection): SQLite database connection object.
        connection_id (str): Connection ID.
        chunk_id (int): Chunk ID.

    Returns:
        tuple: A tuple containing the status and review data DataFrame.
    """
    try:
        name = st.session_state["name"]
        new_id = f"{connection_id}_chunk_{chunk_id}"

        query = f"SELECT * FROM call_annotation_table"
        df = (
            pd.read_sql_query(query, _conn)
            .query("username == @name")
            .query("call_id == @new_id")
            .sort_values(["date", "time"], ascending=[False, False])
            .reset_index(drop=True)
        )

        if df.empty:
            status = "Pending"
        else:
            status = "Reviewed"

        return status, df
    except Exception as e:
        logging.error(f"An error occurred in 'get_already_reviewed_calls': {e}")
        logging.error(traceback.format_exc())
        return None, None


def reviewer_select_connid(review_df):
    """
    Set the current index based on the selected ConnectionID.

    Args:
        review_df (pandas.DataFrame): DataFrame containing the review data.

    Returns:
        None
    """
    try:
        conn_id_select = st.session_state.get("conn_id_select")

        if conn_id_select is not None:
            idx = review_df[review_df["ConnectionID"] == conn_id_select].index[0]
            st.session_state["current_idx"] = idx
    except Exception as e:
        logging.error(f"An error occurred in 'reviewer_select_connid': {e}")
        logging.error(traceback.format_exc())


def reviewer_select_chunkid(review_df):
    """
    Set the current index based on the selected ConnectionID and chunk ID.

    Args:
        review_df (pandas.DataFrame): DataFrame containing the review data.

    Returns:
        None
    """
    try:
        conn_id_select = st.session_state.get("conn_id_select")
        chunk_id_select = st.session_state.get("chunk_id_select")

        if conn_id_select is not None and chunk_id_select is not None:
            idx = review_df[
                (review_df["ConnectionID"] == conn_id_select)
                & (review_df["chunk_id"] == chunk_id_select)
            ].index[0]
            st.session_state["current_idx"] = idx

    except Exception as e:
        logging.error(f"An error occurred in 'reviewer_select_chunkid': {e}")
        logging.error(traceback.format_exc())


def display_annotation_details(current_row):
    """
    Display the annotation details for the current row in the webapp.

    Args:
        current_row (pd.Series): Series containing the current row data.

    Returns:
        None
    """
    try:
        rename_columns = {
            "ConnectionID": "Connection ID",
            "chunk_id": "Chunk ID",
            "Annotator": "Annotator",
            "case_type": "Intent",
            "subcase_type": "Sub-Intent",
            "confidence": "Confidence Level",
            "comments": "Annotator Comments",
        }

        _, dcol, _ = st.columns([1, 2, 1])

        df = (
            current_row.filter(rename_columns.keys())
            .reset_index(name="Details")
            .replace(rename_columns)
            .rename(columns={"index": "Columns"})
        )

        dcol.dataframe(df, use_container_width=True)
    except Exception as e:
        logging.error(f"An error occurred in 'display_annotation_details': {e}")
        logging.error(traceback.format_exc())


def display_name_and_role():
    """
    Display the name and role of the user.

    Returns:
        None
    """
    try:
        _, col1, col2, _ = st.columns([1, 2, 2, 1])

        col1.markdown(
            f"<p style='text-align: left;'><b>Welcome {st.session_state.get('name')}</b></p>",
            unsafe_allow_html=True,
        )

        col2.markdown(
            f"<p style='text-align: right;'><b>Role: {st.session_state.get('role')}</b></p>",
            unsafe_allow_html=True,
        )
    except Exception as e:
        logging.error(f"An error occurred in 'display_name_and_role': {e}")
        logging.error(traceback.format_exc())
