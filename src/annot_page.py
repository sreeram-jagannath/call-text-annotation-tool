import pandas as pd
import streamlit as st

from helper_functions import *


def get_annotator_page(conn, cursor):
    # Centered title using HTML tags
    st.markdown(
        "<h1 style='text-align: center;'>Sunlife Annotation Tool</h1>",
        unsafe_allow_html=True,
    )

    display_name_and_role()

    data, intents, mapping = read_dataframes()
    # data = data[data["ConnectionID"] == "c_202201271611026714"].head()
    data = data.groupby("ConnectionID").head(4).reset_index(drop=True)

    all_intents = get_all_intent_options(intent_df=intents)
    all_subintents = get_all_subintent_options(intent_df=intents)

    already_annotated_df = read_annotated_data(_conn=conn)

    # this can be some chunk of a call too...not necessarily the starting from a new call
    call_ids = get_unannotated_ids(
        call_data=data,
        annotated_df=already_annotated_df,
        user_call_mapping=mapping,
        username=st.session_state.get("name"),
    )

    # store the already annotated data in session state,
    # check if the data has changed due to clearing cache
    # if the data has been changed, then clear required
    # keys from the session state
    if "call_ids_shape" in st.session_state:
        # if current call_ids is not equal to stored one
        # it means the some new user has logged in
        if st.session_state["call_ids_shape"] != call_ids.shape[0]:
            # st.session_state["call_ids_shape"] = call_ids.shape[0]
            # clear out the appropriate keys in session states
            st.session_state["call_ids_shape"] = call_ids.shape[0]
            reset_session_state(calls_df=call_ids)

    else:
        st.session_state["og_total_calls"] = call_ids.shape[0]
        st.session_state["call_ids_shape"] = call_ids.shape[0]

    # st.dataframe(call_ids, use_container_width=True)

    if "all_done" not in st.session_state:
        st.session_state["all_done"] = False

    # st.write(st.session_state)

    if call_ids.empty or st.session_state["all_done"]:
        st.balloons()
        st.success("You don't have any texts to annotate!")
    else:
        # connection_id = connection_ids[0]
        if "annotated_idx" not in st.session_state:
            st.session_state["current_idx"] = 0
            st.session_state["annotated_idx"] = set()

        current_row = call_ids.iloc[st.session_state["current_idx"]]
        current_conn_id = current_row[CONN_ID_COLNAME]

        st.session_state["current_conn_id"] = current_conn_id
        st.session_state["current_chunk_id"] = current_row[CHUNK_ID_COLNAME]

        # st.write(current_row)

        with st.expander(
            label=f"Expand to see full conversation (ConnectionID: {current_conn_id})"
        ):
            full_text = current_row[FULL_TEXT_COLNAME]
            st.text(full_text)

            st.markdown(
                """
                <style>
                div[data-testid='stText'] {
                    background-color: lightyellow;
                    border: 5px;
                    padding: 10px;
                    -webkit-user-select: none; /* Disable text selection on webkit browsers */
                    -moz-user-select: none; /* Disable text selection on Firefox */
                    -ms-user-select: none; /* Disable text selection on Microsoft Edge */
                    user-select: none; /* Disable text selection on other browsers */
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

        diff = st.session_state["og_total_calls"] - st.session_state["call_ids_shape"]
        progress_text = f"Progress: [{len(st.session_state['annotated_idx']) + diff} / {st.session_state['og_total_calls']}]"
        st.progress(
            value=(len(st.session_state["annotated_idx"]) + diff)
            / st.session_state["og_total_calls"],
            text=progress_text,
        )

        st.markdown(
            "<h3 style='text-align: center;'>Annotate chunks</h3>",
            unsafe_allow_html=True,
        )

        # Display connection id and chunk id
        _, col1, col2, _ = st.columns([1, 2, 2, 1])

        col1.markdown(
            f"<p style='text-align: center;'><b>Connection ID: {current_conn_id}</b></p>",
            unsafe_allow_html=True,
        )

        col2.markdown(
            f"<p style='text-align: center;'><b>Chunk ID: {current_row[CHUNK_ID_COLNAME].astype(int)}</b></p>",
            unsafe_allow_html=True,
        )

        # Text display
        _, chunk_col, _ = st.columns([1, 2, 1])
        chunk_col.markdown(
            f"<p style='text-align: justify; padding: 10px; border: 1px solid black; border-radius: 5px; background-color: #D8D8D8; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none;'>{current_row[TEXT_COLNAME]}</p>",
            unsafe_allow_html=True,
        )

        # Dropdowns
        _, scol1, scol2, _ = st.columns([1, 1, 1, 1])
        default_intents = get_default_options(current_row[INTENT_COLNAME])
        # st.write(f"Default Intents: {default_intents}, {st.session_state.get('intent_dropdown')}")
        intent_list = scol1.multiselect(
            label="Intent",
            options=all_intents,
            default=default_intents,
            key=f"intent_dropdown_{current_row['new_id']}",
        )

        valid_subintents = get_valid_subintent_options(
            intent_list=intent_list, subintent_map=all_subintents
        )
        default_subintents = get_default_options(current_row[SUB_INTENT_COLNAME])
        final_default_subintents = list(
            set(valid_subintents).intersection(set(default_subintents))
        )

        # st.write(f"Valid Subintents: {valid_subintents} || Default Subintents: {default_subintents} Final Default: {final_default_subintents}")
        subintent_list = scol2.multiselect(
            label="Sub Intent",
            options=valid_subintents,
            default=final_default_subintents,
            key=f"subintent_dropdown_{current_row['new_id']}",
        )

        _, conf_col, _ = st.columns([1, 2, 1])
        confidence_level = conf_col.selectbox(
            label="Confidence",
            options=["High", "Medium", "Low"],
            key=f"conf_sel_{current_row['new_id']}",
        )

        _, textcol, _ = st.columns([1, 2, 1])
        user_comments = textcol.text_area(
            label="Comments", key=f"comment_{current_row['new_id']}", height=10
        )

        # st.write(st.session_state)

        st.markdown(
            "<h4 style='text-align: center;'>Final selection</h4>",
            unsafe_allow_html=True,
        )

        # display choices in columns
        _, ccol1, ccol2, _ = st.columns([1, 2, 2, 1])
        ccol1.info(f"**Intents**: {intent_list}")
        ccol2.warning(f"**Sub Intents**: {subintent_list}")

        st.title("")
        _, bcol1, bcol2, bcol3, _ = st.columns([1.5, 1, 1, 1, 1])

        # st.write(st.session_state)
        # if st.session_state["current_idx"] > 0:
        bcol1.button("Previous", on_click=previous_button_clicked)

        # if done with all the chunks for the user, don't show the save and next button
        # if st.session_state["current_idx"] + 1 < len(call_ids):
        bcol2.button("Next", on_click=next_button_clicked)

        bcol3.button(
            "Save and Next",
            on_click=save_next_button_clicked,
            args=(
                conn,
                cursor,
                current_row["new_id"],
                intent_list,
                subintent_list,
                confidence_level,
                user_comments,
            ),
        )

        st.divider()

        select_data_query = "SELECT * FROM call_annotation_table"
        df = pd.read_sql_query(select_data_query, conn).sort_values(
            by=["date", "time"], ascending=False
        )
        st.subheader("Database")
        st.dataframe(df, use_container_width=True)

        with st.expander(label="Guidelines to use the dashboard"):
            show_pdf(file_path="../sample.pdf")
