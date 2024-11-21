# Use an official Python base image
FROM python:3.11-slim

# Install system dependencies, including FFmpeg and ImageMagick
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify that ImageMagick was installed correctly
RUN convert -version
RUN which convert

# Set the working directory
WORKDIR /app

# Modify ImageMagick policy file to remove restrictions on certain patterns
RUN sed -i '/<policy domain="path" rights="none" pattern="@\*"/d' /etc/ImageMagick-6/policy.xml

# Debug: Print the contents of the policy file to verify the changes
RUN cat /etc/ImageMagick-6/policy.xml

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
