# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY data_requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN apt-get update \
    && apt-get install -y build-essential python3-dev \
    && pip install --no-cache-dir -r data_requirements.txt

# Copy the application files
COPY db_app.py /app/app.py

# Copy the data
COPY chroma_db_default_emb /app/data/chroma_db_default_emb
COPY queries.db /app/data/queries.db


# Expose the port on which the FastAPI app will run
EXPOSE 8001

# Command to run the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
