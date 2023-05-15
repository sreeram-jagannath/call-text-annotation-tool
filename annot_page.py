import streamlit as st
import pandas as pd


@st.cache_data
def get_unannotated_ids(call_data, user_call_mapping, username):
    call_ids = (
        pd.merge(call_data, user_call_mapping, on="ConnectionID", how="left")
        .query("Annotator == @username")
        .assign(new_id = lambda x: x["ConnectionID"] + "_chunk_" + x["chunk_id"].astype(str))
        .sort_values(by=["ConnectionID", "chunk_id"])
        .reset_index(drop=True)
    )

    return call_ids


@st.cache_data
def read_dataframes():
    data = pd.read_parquet("./inputs/data.parquet")
    intents = pd.read_parquet("./inputs/intents.parquet")
    mapping = pd.read_parquet("./inputs/mapping.parquet")

    return data, intents, mapping


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


def previous_button_clicked():
    idx = st.session_state["previous_idx"].pop()
    st.session_state["current_idx"] = idx


def next_button_clicked():
    st.session_state["previous_idx"].append(st.session_state["current_idx"])
    st.session_state["current_idx"] += 1


def save_next_button_clicked():
    st.session_state["current_idx"] += 1


def get_default_options(values):
    if values is None:
        return []
    
    options = [s.strip() for s in values.split(',')]
    return options


def get_annotator_page():
    # Centered title using HTML tags
    st.markdown("<h1 style='text-align: center;'>Sunlife Annotation Tool</h1>", unsafe_allow_html=True)
    st.write(f'Welcome *{st.session_state.get("name")}*')
    st.write(f"Role: {st.session_state.get('role')}")

    data, intents, mapping = read_dataframes()
    all_intents = get_all_intent_options(intent_df=intents)
    all_subintents = get_all_subintent_options(intent_df=intents)

    # this can be some chunk of a call too...not necessarily the starting from a new call
    call_ids = get_unannotated_ids(
        call_data=data, 
        user_call_mapping=mapping, 
        username=st.session_state.get("name"),
    )

    # st.write(call_ids)

    if call_ids.empty:
        st.success("You don't have any texts to annotate!")
    else:
        # connection_id = connection_ids[0]
        if "current_idx" not in st.session_state:
            st.session_state["current_idx"] = 0
            st.session_state["previous_idx"] = []     # stack


        current_row = call_ids.iloc[st.session_state["current_idx"]]
        current_conn_id = current_row["ConnectionID"]

        # st.write(current_row)

        with st.expander(label=f"Expand to see full conversation (ConnectionID: {current_conn_id})"):
            full_text = current_row["full_text"]
            st.text(full_text)

        st.markdown("<h3 style='text-align: center;'>Annotate chunks</h3>", unsafe_allow_html=True)

        # Text display
        st.markdown(f"<p style='text-align: center;'>{current_row['text']}</p>", unsafe_allow_html=True)
        st.title("")

        # st.write(current_row["Call Type"].split(','), all_intents)
        # st.write(all_intents, [] if current_row["Call Type"] is None else current_row["Call Type"].split(','))
    

        # Dropdowns
        _, scol1, scol2, _ = st.columns([1, 1, 1, 1])
        default_intents = get_default_options(current_row["Call Type"])
        # st.write(f"Default Intents: {default_intents}, {st.session_state.get('intent_dropdown')}")
        intent_list = scol1.multiselect(
            label="Intent", 
            options=all_intents,
            default=default_intents,
            key=f"intent_dropdown_{current_row['new_id']}",
        )

        valid_subintents = get_valid_subintent_options(intent_list=intent_list, subintent_map=all_subintents)
        default_subintents = get_default_options(current_row["Call SubType"])
        final_default_subintents = list(set(valid_subintents).intersection(set(default_subintents)))

        # st.write(f"Valid Subintents: {valid_subintents} || Default Subintents: {default_subintents} Final Default: {final_default_subintents}")
        subintent_list = scol2.multiselect(
            label="Sub Intent", 
            options=valid_subintents,
            default=final_default_subintents,
            key=f"subintent_dropdown_{current_row['new_id']}",
        )

        # st.write(st.session_state)

        st.markdown("<h4 style='text-align: center;'>Final selection</h4>", unsafe_allow_html=True)

        # display choices in columns
        _, ccol1, ccol2, _ = st.columns([1, 2, 2, 1])
        ccol1.info(f"**Intents**: {intent_list}")
        ccol2.warning(f"**Sub Intents**: {subintent_list}")

        st.title("")
        _, bcol1, bcol2, bcol3, _ = st.columns([1.5, 1, 1, 1, 1])

        if st.session_state["previous_idx"] != []:
            bcol1.button("Previous", on_click=previous_button_clicked)

        bcol2.button("Next", on_click=next_button_clicked)
        bcol3.button("Save and Next", on_click=save_next_button_clicked)

            