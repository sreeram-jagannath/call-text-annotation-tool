import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from annot_page import get_annotator_page
from review_page import get_reviewer_page

from helper_functions import *

page_icon_img = "images/sunlife.png"
st.set_page_config(
    page_title="Intent Dectection | Data Labeling Testing",
    layout="wide",
    page_icon=page_icon_img,
    initial_sidebar_state="collapsed",
)

with open('./utils/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)


authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)



if __name__ == "__main__":
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        authenticator.logout('Logout', 'sidebar')
        role = config.get("credentials").get("usernames").get(username).get("role")
        
        st.session_state["name"] = name
        st.session_state["role"] = role

        conn, cursor = init_connection()

        if role == "annotator":
            get_annotator_page(conn=conn, cursor=cursor)
        elif role == "reviewer":
            get_reviewer_page(conn=conn, cursor=cursor)

        @atexit.register
        def close_db():
            close_database(cursor=cursor, connection=conn)

    elif authentication_status is False:
        st.error('Username/password is incorrect')

    elif authentication_status is None:
        st.warning('Please enter your username and password')
