import subprocess

# Run streamlit
streamlit_process = subprocess.Popen(["streamlit", "hello"], stdout=subprocess.DEVNULL)

# Run ngrok
ngrok_process = subprocess.Popen(["ngrok", "http", "8501"])

# Wait for both processes to finish
streamlit_process.wait()
ngrok_process.wait()
