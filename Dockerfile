# Start from the official Python base image.
FROM python:3.9

# Copy the src directory into the container
COPY ./src /src

# Copy .env file into the container at /src
COPY .env /src

# Copy static directory into the container at /src
COPY static /src/static

# Set the working directory to /src
WORKDIR /src

# Copy the requierements file into the container at /src
COPY requirements.txt /src

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

# Install Nginx
RUN apt-get update && apt-get install -y nginx

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
CMD service nginx start && uvicorn main:app --host 0.0.0.0 --port 8000
