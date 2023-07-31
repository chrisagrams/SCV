# Start from official Ubuntu image
FROM ubuntu:22.04

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

# Install Nginx, Python, and PyMOL
RUN apt-get update && apt-get install -y nginx python3 python3-pip pymol

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

# Create nginx group and user
RUN groupadd -r nginx && useradd -r -g nginx nginx

# Remove the default Nginx configuration file
RUN rm -v /etc/nginx/nginx.conf

# Copy the custom Nginx configuration file
COPY nginx.conf /etc/nginx/nginx.conf

# Set permissions for static directory
RUN chown -R nginx:nginx /src/static

# Validate the Nginx configuration
RUN nginx -t

# Set the command to start Nginx and run the uvicorn server
CMD service nginx start && uvicorn src.main:app --host 0.0.0.0 --port 8000
