FROM python:3.11-slim

WORKDIR /app

# Install dependencies before copying raw code to cache Docker layers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fpdf2 apscheduler

# Copy application configuration and routers
COPY . .

# Expose backend port
EXPOSE 8000

# Start Uvicorn 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
