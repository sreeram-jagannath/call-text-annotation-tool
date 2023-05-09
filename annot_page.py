import streamlit as st


def get_annotator_page():

    st.write(f'Welcome *{st.session_state.get("name")}*')
    st.write(f"Role: {st.session_state.get('role')}")

