# Start from official Ubuntu image
FROM ubuntu:22.04

# Install Python, and PyMOL
RUN apt-get update && apt-get install -y python3 python3-pip pymol

RUN mkdir /scv

# Copy the requierements file into the container at /src
COPY requirements.txt /scv

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /scv/requirements.txt

# Copy the scv directory into the container
COPY ./scv /scv

# Copy .env file into the container
COPY .env /scv

# Copy static directory into the container at /scv
COPY static /scv/static

# Copy vendor directory into the container at /scv
COPY vendor /scv/vendor

# Copy rates.json
COPY rates.json /scv

# Make db directory
RUN mkdir /db

WORKDIR /scv

# Set the command  run the uvicorn server
CMD uvicorn main:app --host 0.0.0.0 --port 8000
