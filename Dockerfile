# Start from official Ubuntu image
FROM ubuntu:22.04

# Install Python, and PyMOL
RUN apt-get update && apt-get install -y python3 python3-pip pymol

# Copy the src directory into the container
COPY ./src /src

# Copy .env file into the container
COPY .env ./

# Copy static directory into the container at /src
COPY static /src/static

# Copy vendor directory into the container at /src
COPY vendor /src/vendor

# Copy rates.json
COPY rates.json ./

# Make db directory
RUN mkdir /db

# Copy the requierements file into the container at /src
COPY requirements.txt /src

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

# Set the command  run the uvicorn server
CMD uvicorn src.main:app --host 0.0.0.0 --port 8000
