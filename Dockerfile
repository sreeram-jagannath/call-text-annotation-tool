# Use Python 3.8 as the base image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app

# Clone the repository from GitHub
RUN apt-get update && apt-get install -y git
RUN git clone https://github.com/sreeram-jagannath/call-text-annotation-tool.git .

# Create and activate a virtual environment
RUN python -m venv annotator-webapp-env
RUN /bin/bash -c "source annotator-webapp-env/bin/activate"

# Install the required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port used by Streamlit
EXPOSE 8501

# Set the command to run the Streamlit application
CMD streamlit run app.py & ngrok http 8501
