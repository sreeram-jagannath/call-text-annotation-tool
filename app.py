import base64
import os
import pickle
import random
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth

page_icon_img = "images/sunlife.png"
st.set_page_config(
    page_title="Intent Dectection | Data Labeling Testing",
    layout="wide",
    page_icon=page_icon_img,
    initial_sidebar_state="collapsed",
)

if __name__ == "__main__":
    st.title("Hello world!")
