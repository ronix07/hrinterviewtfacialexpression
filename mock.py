import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import time
import webbrowser
import os
import subprocess
import socket
import sys

# Set page configuration
st.set_page_config(
    page_title="StressIQ login ",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide the default Streamlit header and footer
st.markdown("""
    <style>
        header {display: none !important;}
        footer {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

# Custom CSS with new purple color scheme
st.markdown("""
<style>
    /* Global styles */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #211C84 0%, #4B47B3 25%, #6B67C7 50%, #8A86DB 75%, #A9A5EF 100%);
        color: white;
    }
    
    /* Navigation bar */
    [data-testid="stHeader"] {
        display: none;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: white !important;
        font-family: 'Segoe UI', sans-serif !important;
        font-weight: 600 !important;
        text-align: center;
    }
    
    h1 {
        font-size: 3rem !important;
        margin-bottom: 2rem !important;
        padding-top: 2rem !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* Buttons */
    .stButton > button {
        background-color: #211C84 !important;
        color: white !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 0.8rem 2rem !important;
        border: 2px solid #4B47B3 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin: 0.5rem 0 !important;
        font-size: 1.1rem !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.3) !important;
        background-color: #4B47B3 !important;
        border-color: #6B67C7 !important;
    }
    
    /* Card containers */
    .card {
        background-color: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        margin: 2rem 0 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Form inputs */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #6B67C7 !important;
        box-shadow: 0 0 0 2px rgba(107, 103, 199, 0.3) !important;
    }

    /* Radio buttons */
    .stRadio > div {
        background-color: rgba(255, 255, 255, 0.1) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin: 1rem 0 !important;
    }

    .stRadio label {
        color: white !important;
        font-size: 1.1rem !important;
    }

    /* Description text */
    .desc-text {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }

    /* Remove default Streamlit padding */
    .main > div {
        padding-top: 0 !important;
    }

    .stApp {
        margin-top: -4rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(r"D:\projects\deployment\mock-20306-firebase-adminsdk-fbsvc-e03a8e8956.json")
    firebase_admin.initialize_app(cred)

# Main App
st.title("Welcome to StressIQ")
st.markdown('<p class="desc-text">Enhance your interview performance with AI-powered stress analysis</p>', unsafe_allow_html=True)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'main'
if 'selected_role' not in st.session_state:
    st.session_state.selected_role = None

# Utility function to check if a port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Main selection page
if st.session_state.page == 'main':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Choose Your Role")
        
        if st.button("👤 I am a Candidate", key="candidate_select"):
            st.session_state.page = 'candidate_login'
            st.session_state.selected_role = 'candidate'
            st.rerun()
            
        if st.button("👥 I am an Interviewer", key="interviewer_select"):
            st.session_state.page = 'interviewer_login'
            st.session_state.selected_role = 'interviewer'
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

# Candidate Login Page
elif st.session_state.page == 'candidate_login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Candidate Portal")
        
        # Toggle between Login and Register
        auth_action = st.radio("", ("Login", "Register"), horizontal=True)
        
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if auth_action == "Register":
            password_confirm = st.text_input("Confirm Password", type="password")
            if st.button("Create Account", key="candidate_register"):
                if password == password_confirm:
                    try:
                        user = auth.create_user(email=email, password=password)
                        st.success("Account created successfully! Please login.")
                        time.sleep(2)
                        st.session_state.page = 'candidate_login'
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Passwords do not match!")
        else:
            if st.button("Login", key="candidate_login"):
                try:
                    user = auth.get_user_by_email(email)
                    st.success("Login Successful! Redirecting to interview platform...")

                    # Start React app in background if not running
                    if not is_port_in_use(5173):
                        creationflags = subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                        subprocess.Popen(
                            ["npm", "run", "dev"],
                            cwd="D:/projects/deployment/aidriven",
                            shell=True,
                            creationflags=creationflags
                        )
                    # Open the browser immediately
                    webbrowser.open("http://localhost:5173")
                    st.info("If the page is blank, please wait a few seconds and refresh. The interview platform is starting in the background.")
                except Exception as e:
                    st.error(f"Login Failed: {e}")
        
        if st.button("← Back to Main Menu", key="candidate_back"):
            st.session_state.page = 'main'
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

# Interviewer Login Page
elif st.session_state.page == 'interviewer_login':
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Interviewer Portal")
        
        # Only Login, no Register
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", key="interviewer_login"):
            try:
                user = auth.get_user_by_email(email)
                st.success("Login Successful! Redirecting to interviewer dashboard...")
                # Start app.py in the background if not already running
                if not is_port_in_use(8502):
                    subprocess.Popen(
                        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port=8502"],
                        shell=True
                    )
                    time.sleep(3)  # Give it a moment to start
                webbrowser.open("http://localhost:8502")
            except Exception as e:
                st.error(f"Login Failed: {e}")
        
        if st.button("\u2190 Back to Main Menu", key="interviewer_back"):
            st.session_state.page = 'main'
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
                
                
                