# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code
# This includes src/, accs.txt, and proxies.txt
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the API with Uvicorn
# The --host 0.0.0.0 is crucial to make the server accessible from outside the container
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"] 