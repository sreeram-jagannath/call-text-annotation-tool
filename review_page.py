import streamlit as st

from helper_functions import *


def get_reviewer_page(conn, cursor):
    st.markdown(
        "<h1 style='text-align: center;'>Sunlife Annotation Tool</h1>",
        unsafe_allow_html=True,
    )

    display_name_and_role()

    data, intents, mapping = read_dataframes()
    all_intents = get_all_intent_options(intent_df=intents)
    all_subintents = get_all_subintent_options(intent_df=intents)

    already_annotated_df = read_annotated_data(_conn=conn)

    # this can be some chunk of a call too...not necessarily the starting from a new call
    review_call_ids = get_call_ids_to_be_reviewed(
        call_data=data,
        user_call_mapping=mapping,
        annot_data=already_annotated_df,
        rev_username=st.session_state.get("name"),
    )

    # st.write(annot_data)
    # st.write(review_call_ids)

    if review_call_ids.empty:
        st.success("You don't have any texts to review!")
        st.balloons()
    else:
        if "current_idx" not in st.session_state:
            st.session_state["current_idx"] = 0
            st.session_state["n_chunks"] = review_call_ids.shape[0]
            st.session_state["annotated_idx"] = set()

        current_row = review_call_ids.iloc[st.session_state["current_idx"]]
        current_conn_id = current_row["ConnectionID"]
        current_chunk_id = current_row["chunk_id"]

        if "conn_id_select" in st.session_state:
            st.session_state["conn_id_select"] = current_conn_id

        if "chunk_id_select" in st.session_state:
            st.session_state["chunk_id_select"] = current_chunk_id

        conn_id_list = review_call_ids["ConnectionID"].unique().tolist()
        chunk_id_list = (
            review_call_ids[review_call_ids["ConnectionID"] == current_conn_id][
                "chunk_id"
            ]
            .unique()
            .tolist()
        )

        _, fcol1, fcol2, _ = st.columns([1, 2, 2, 1])
        fcol1.selectbox(
            "Connection ID",
            options=conn_id_list,
            key="conn_id_select",
            on_change=reviewer_select_connid,
            args=(review_call_ids,),
        )
        fcol2.selectbox(
            "Chunk ID",
            options=chunk_id_list,
            key="chunk_id_select",
            on_change=reviewer_select_chunkid,
            args=(review_call_ids,),
        )

        with st.expander(
            label=f"Expand to see full conversation (ConnectionID: {current_conn_id})"
        ):
            full_text = current_row["full_text"]
            st.text(full_text)

            st.markdown(
                "<style>div[data-testid='stText'] {background-color: lightyellow; border: 5px; padding: 10px}",
                unsafe_allow_html=True,
            )

        # Text display
        _, chunk_col, _ = st.columns([1, 2, 1])
        chunk_col.markdown(
            f"<p style='text-align: justify; padding: 10px; border: 1px solid black; border-radius: 5px; background-color: #D8D8D8;'>{current_row['text']}</p>",
            unsafe_allow_html=True,
        )
        # st.write(f"ConnectionID: {current_conn_id} ChunkID: {current_row['chunk_id']}", )

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
        else:
            default_subintents = get_default_options(
                reviewed_df.iloc[0]["subcase_type"]
            )

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
        reviewer_comments = textcol.text_area(
            label="Reviewer Comments", key=f"comment_{current_row['new_id']}", height=10
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

        # if st.button("close_database"):
        #     cursor.close()
        #     conn.close()
        #     st.stop()

        if st.button("Read Database"):
            query = f"SELECT * FROM call_annotation_table"
            df = pd.read_sql_query(query, conn)

            st.write(df)

    @atexit.register
    def close_db():
        try:
            close_database(cursor=cursor, connection=conn)
        except:
            pass
