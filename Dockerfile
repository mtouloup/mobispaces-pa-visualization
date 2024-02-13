FROM python:3.9.16-slim

# Create a directory for the source files
RUN mkdir /usr/src/app

# Set the working directory to /app
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /app
COPY ./requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# Copy the application source code
COPY . .

#Expose Port
EXPOSE 80

ENTRYPOINT ["python3", "/usr/src/app/app.py"]
