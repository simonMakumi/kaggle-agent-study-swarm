# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
# (We don't put the key here for security, we pass it at runtime)
ENV GOOGLE_API_KEY=your_key_here

# Run app.py when the container launches
CMD ["python", "main.py"]
