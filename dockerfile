# Use an official Python base image
FROM python:3.11-slim

# Install system dependencies, including FFmpeg and ImageMagick
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y imagemagick

# Set the working directory
WORKDIR /app

# Set the policy for ImageMagick (fix security policy for certain formats if needed)
RUN echo "<policy domain=\"coder\" rights=\"read|write\" pattern=\"PDF\" />" >> /etc/ImageMagick-6/policy.xml

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the working directory
COPY . .

# Expose the FastAPI default port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
