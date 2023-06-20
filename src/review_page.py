import streamlit as st

from helper_functions import *


def get_reviewer_page(conn, cursor):
    st.markdown(
        "<h1 style='text-align: center;'>Sunlife Annotation Tool</h1>",
        unsafe_allow_html=True,
    )

    display_name_and_role()

    data, intents, mapping = read_dataframes()
    data = data.groupby("ConnectionID").head(4).reset_index(drop=True)

    all_intents = get_all_intent_options(intent_df=intents)
    all_subintents = get_all_subintent_options(intent_df=intents)

    already_annotated_df = read_annotated_data(_conn=conn)

    # this can be some chunk of a call too...not necessarily the starting from a new call
    all_review_call_ids = get_call_ids_to_be_reviewed(
        call_data=data,
        user_call_mapping=mapping,
        annot_data=already_annotated_df,
        rev_username=st.session_state.get("name"),
    )

    _, cf1, _ = st.columns([2, 2, 1])
    cf1.checkbox(
        "Filter only calls with Low/Medium confidence",
        value=True,
        key="conf_filter",
        on_change=conf_checkbox_func,
    )
    if st.session_state["conf_filter"]:
        review_call_ids = all_review_call_ids[
            all_review_call_ids["confidence"] != "High"
        ].reset_index(drop=True)
    else:
        review_call_ids = all_review_call_ids.copy()

    # st.dataframe(review_call_ids, use_container_width=True)

    # store the already annotated data in session state,
    # check if the data has changed due to clearing cache
    # if the data has been changed, then clear required
    # keys from the session state
    if "call_ids_shape" in st.session_state:
        # if current call_ids is not equal to stored one
        # it means the some new user has logged in
        if st.session_state["call_ids_shape"] != all_review_call_ids.shape[0]:
            # st.session_state["call_ids_shape"] = call_ids.shape[0]
            # clear out the appropriate keys in session states
            st.session_state["call_ids_shape"] = all_review_call_ids.shape[0]
            reset_session_state(calls_df=review_call_ids)

    else:
        st.session_state["current_idx"] = 0
        st.session_state["call_ids_shape"] = all_review_call_ids.shape[0]

    # st.write(st.session_state)

    # st.write(st.session_state.get("current_idx"), "after reset_session")

    if review_call_ids.empty:
        st.success("You don't have any texts to review!")
        st.balloons()
    else:
        current_row = review_call_ids.iloc[st.session_state["current_idx"]]
        current_conn_id = current_row[CONN_ID_COLNAME]
        current_chunk_id = current_row[CHUNK_ID_COLNAME]
        # print(current_conn_id, current_chunk_id)

        st.session_state["current_conn_id"] = current_conn_id
        st.session_state["current_chunk_id"] = current_chunk_id

        if "conn_id_select" in st.session_state:
            st.session_state["conn_id_select"] = current_conn_id

        if "chunk_id_select" in st.session_state:
            st.session_state["chunk_id_select"] = current_chunk_id

        conn_id_list = review_call_ids[CONN_ID_COLNAME].unique().tolist()
        chunk_id_list = (
            review_call_ids[review_call_ids[CONN_ID_COLNAME] == current_conn_id][
                CHUNK_ID_COLNAME
            ]
            .unique()
            .tolist()
        )

        # st.write(f"{st.session_state.get('current_idx')=}")
        # st.write(f"{st.session_state.get('current_conn_id')=}")
        # st.write(f"{st.session_state.get('current_chunk_id')=}")
        # st.write(f"{st.session_state.get('conn_id_select')=}")
        # st.write(f"{st.session_state.get('chunk_id_select')=}")



        # conn_sel_idx = conn_id_list.index()
        # print(
        #     conn_id_list,
        #     chunk_id_list,
        #     conn_id_list.index(current_conn_id),
        #     chunk_id_list.index(current_chunk_id),
        # )
        _, fcol1, fcol2, _ = st.columns([1, 2, 2, 1])
        fcol1.selectbox(
            "Connection ID",
            options=conn_id_list,
            index=conn_id_list.index(current_conn_id),
            key="conn_id_select",
            on_change=reviewer_select_connid,
            args=(review_call_ids,),
        )
        # print('passed connection dropdown')

        fcol2.selectbox(
            "Chunk ID",
            options=chunk_id_list,
            index=chunk_id_list.index(current_chunk_id),
            key="chunk_id_select",
            on_change=reviewer_select_chunkid,
            args=(review_call_ids,),
        )

        # print('passed both dropdowns')

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

        # Text display
        _, chunk_col, _ = st.columns([1, 2, 1])
        chunk_col.markdown(
            f"<p style='text-align: justify; padding: 10px; border: 1px solid black; border-radius: 5px; background-color: #D8D8D8; -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none;'>{current_row[TEXT_COLNAME]}</p>",
            unsafe_allow_html=True,
        )
        # st.write(f"ConnectionID: {current_conn_id} ChunkID: {current_row[CHUNK_ID_COLNAME]}", )

        _, icol, _ = st.columns([1, 2, 1])
        icol.info("**Annotation Details**")

        display_annotation_details(current_row=current_row)

        review_status, reviewed_df = get_already_reviewed_calls(
            _conn=conn, connection_id=current_conn_id, chunk_id=current_chunk_id
        )

        _, scol, _ = st.columns([1, 2, 1])
        if review_status == "Pending":
            default_intents = get_default_options(current_row["case_type"])
            scol.warning(f"Reviewer Status: {review_status}")

        else:
            default_intents = get_default_options(reviewed_df.iloc[0]["case_type"])
            scol.success(f"Reviewer Status: {review_status}")

        # st.table(reviewed_df)

        # Dropdowns
        _, scol1, scol2, _ = st.columns([1, 1, 1, 1])
        # default_intents = get_default_options(current_row["case_type"])
        intent_list = scol1.multiselect(
            label="Intent",
            options=all_intents,
            default=default_intents,
            key=f"intent_dropdown_{current_row['new_id']}",
        )

        valid_subintents = get_valid_subintent_options(
            intent_list=intent_list, subintent_map=all_subintents
        )

        if review_status == "Pending":
            default_subintents = get_default_options(current_row["subcase_type"])
            conf_idx = 0
            reviewer_comments = ""

        else:
            default_subintents = get_default_options(
                reviewed_df.iloc[0]["subcase_type"]
            )

            conf_idx_map = {
                "High": 0,
                "Medium": 1,
                "Low": 2,
            }
            reviewer_confidence = reviewed_df.iloc[0]["confidence"]
            conf_idx = conf_idx_map.get(reviewer_confidence)

            reviewer_comments = reviewed_df.iloc[0]["comments"]

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
            index=conf_idx,
            key=f"conf_sel_{current_row['new_id']}",
        )

        _, textcol, _ = st.columns([1, 2, 1])
        reviewer_comments = textcol.text_area(
            label="Reviewer Comments",
            key=f"comment_{current_row['new_id']}",
            height=10,
            value=reviewer_comments,
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

        if st.session_state["current_idx"] > 0:
            bcol1.button("Previous", on_click=previous_button_clicked_reviewer)

        # if done with all the chunks for the user, don't show the save and next button
        # if st.session_state["current_idx"] + 1 < len(call_ids):
        bcol2.button("Next", on_click=next_button_clicked_reviewer)

        bcol3.button(
            "Save and Next",
            on_click=save_next_button_clicked_reviewer,
            args=(
                conn,
                cursor,
                current_row["new_id"],
                intent_list,
                subintent_list,
                confidence_level,
                reviewer_comments,
            ),
        )

        # if st.button("Read Database"):
        #     query = f"SELECT * FROM call_annotation_table"
        #     df = pd.read_sql_query(query, conn)

        #     st.write(df)
        st.divider()

        select_data_query = "SELECT * FROM call_annotation_table"
        df = pd.read_sql_query(select_data_query, conn).sort_values(
            by=["date", "time"], ascending=False
        )
        st.subheader("Database")
        st.dataframe(df, use_container_width=True)

        with st.expander(label="Guidelines to use the dashboard"):
            show_pdf(file_path="../sample.pdf")

        # print("*" * 20)
