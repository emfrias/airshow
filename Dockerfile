# Use the official Python image
FROM python:3.12.5

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install pg_isready
RUN apt-get update && apt-get -y install postgresql-client

# Copy the wait-for-it script
COPY wait-for-it.sh /app/wait-for-it.sh

# Copy the rest of the application code
COPY . .

# Expose the port that the app runs on
EXPOSE 7878

# Run the application with wait-for-it to ensure DB is up
CMD ["./wait-for-it.sh", "db", "--", "python", "main.py"]
