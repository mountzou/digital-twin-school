# Use official lightweight Python image
FROM python:3.9-slim

# Prevent Python from writing .pyc and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory inside the container
WORKDIR /app

# Copy only requirements first (better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Tell Flask which app to run
ENV FLASK_APP=app.py

# Run the Flask development server (Render will still put it behind a proxy)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]