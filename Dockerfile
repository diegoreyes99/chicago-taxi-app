# Base Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy files to container
COPY requirements.txt .
COPY app.py .
# IMPORTANT: The model is copied here, but the CSVs stay in the cloud
COPY modelo_taxi_river.pkl .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
