FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# Make the startup script executable
RUN chmod +x start.sh

EXPOSE 8000

# start.sh runs migrations then launches uvicorn
CMD ["./start.sh"]
