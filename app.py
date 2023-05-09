import base64
import os
import pickle
import random
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader

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
        st.write(f'Welcome *{name}*')
        st.title('Some content')
    elif authentication_status is False:
        st.error('Username/password is incorrect')
    elif authentication_status is None:
        st.warning('Please enter your username and password')
