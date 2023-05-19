import streamlit as st
import sqlite3
import pandas as pd

from datetime import datetime


@st.cache_resource
def init_connection():
    # Connect to the database (creates a new database if it doesn't exist)
    conn = sqlite3.connect("./outputs/annotations_db.db", check_same_thread=False)
    cursor = conn.cursor()

    return conn, cursor


@st.cache_data
def get_unannotated_ids(call_data, annotated_df, user_call_mapping, username):
    call_ids = (
        pd.merge(call_data, user_call_mapping, on="ConnectionID", how="left")
        .query("Annotator == @username")
        .assign(
            new_id=lambda x: x["ConnectionID"] + "_chunk_" + x["chunk_id"].astype(str)
        )
        .sort_values(by=["ConnectionID", "chunk_id"])
        .reset_index(drop=True)
    )

    # st.write("annotated", annotated_df.shape, annotated_df)

    # perform outer join
    outer = call_ids.merge(
        annotated_df, left_on="new_id", right_on="call_id", how="outer", indicator=True
    )
    # st.write("Outer", outer.shape, outer)

    # st.write("call data", call_data.shape, call_data)
    # perform anti-join
    anti_join = outer[(outer._merge == "left_only")].drop("_merge", axis=1)
    # st.write("Anti-Join", anti_join.shape, anti_join)

    return anti_join


@st.cache_data
def read_dataframes():
    data = pd.read_parquet("./inputs/data.parquet")
    intents = pd.read_parquet("./inputs/intents.parquet")
    mapping = pd.read_parquet("./inputs/mapping.parquet")

    return data, intents, mapping


@st.cache_data
def read_annotated_data(_conn):
    select_data_query = f"SELECT * FROM call_annotation_table"
    df = pd.read_sql_query(select_data_query, _conn)

    return df


@st.cache_data
def read_reviewed_data(_conn):
    select_data_query = "SELECT * FROM reviewer_table"
    df = pd.read_sql_query(select_data_query, _conn)

    return df


@st.cache_data
def get_all_intent_options(intent_df):
    all_intents = intent_df["Intent"].unique().tolist()
    return all_intents


@st.cache_data
def get_all_subintent_options(intent_df):
    si_map = intent_df.groupby("Intent")["Sub Intent"].unique().to_dict()
    sub_intent_map = {k: list(v) for k, v in si_map.items()}

    return sub_intent_map


def get_valid_subintent_options(intent_list, subintent_map):
    sub_intent_list = []
    for intent in intent_list:
        sub_intent_list.extend(subintent_map.get(intent))

    return sub_intent_list


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

def previous_button_clicked_reviewer():
    idx = st.session_state["current_idx"] - 1

    if idx == -1:
        idx = st.session_state["n_chunks"] - 1
    
    st.session_state["current_idx"] = idx


def next_button_clicked_reviewer():
    idx = st.session_state["current_idx"] + 1

    if idx == st.session_state["n_chunks"]:
        idx = 0

    st.session_state["current_idx"] = idx
    

def save_next_button_clicked_reviewer(
    conn, cursor, new_id, selected_intents, selected_subintents, confidence, comment
):
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


def previous_button_clicked():
    idx = st.session_state["current_idx"] - 1

    while True:
        if idx == -1:
            idx = st.session_state["n_chunks"] - 1
        if idx not in st.session_state["annotated_idx"]:
            st.session_state["current_idx"] = idx
            break
        idx -= 1


def next_button_clicked():
    idx = st.session_state["current_idx"] + 1

    while True:
        if idx == st.session_state["n_chunks"]:
            idx = 0
        if idx not in st.session_state["annotated_idx"]:
            st.session_state["current_idx"] = idx
            break
        idx += 1


def save_next_button_clicked(
    conn, cursor, new_id, selected_intents, selected_subintents, confidence, comment
):
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


def get_default_options(values):
    if values is None or values == "":
        return []

    options = [s.strip() for s in values.split(",")]
    return options


def get_call_ids_to_be_reviewed(call_data, user_call_mapping, annot_data, rev_username):
    ...
    """
    read all possible calls
    merge the mapping data to get the reviewer
    merge it with annotated data
    """

    only_annotator_data = annot_data.query("role == 'annotator'")
    only_reviewer_data = annot_data.query("role == 'reviewer'")

    call_ids = (
        pd.merge(call_data, user_call_mapping, on="ConnectionID", how="left")
        .query("Reviewer == @rev_username")
        .assign(
            new_id=lambda x: x["ConnectionID"] + "_chunk_" + x["chunk_id"].astype(str)
        )
        .merge(
            only_annotator_data, left_on=["new_id"], right_on=["call_id"], how="inner"
        )
        .sort_values(by=["ConnectionID", "chunk_id"])
        .reset_index(drop=True)
    )

    # st.write("call data", call_data.shape, call_data)

    # perform outer join
    # outer = call_ids.merge(annotated_df, left_on="new_id", right_on='call_id', how='outer', indicator=True)
    # st.write(outer)

    # #perform anti-join
    # anti_join = outer[(outer._merge=='both')].drop('_merge', axis=1)
    # st.write(anti_join.head())

    # st.write("call ids", call_ids.shape, call_ids)

    return call_ids


def get_already_reviewed_calls(_conn, connection_id, chunk_id):
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


def reviewer_select_connid(review_df):
    st.write(f"{st.session_state['conn_id_select']=}")

    st.session_state["current_idx"] = review_df[
        review_df["ConnectionID"] == st.session_state["conn_id_select"]
    ].index[0]
