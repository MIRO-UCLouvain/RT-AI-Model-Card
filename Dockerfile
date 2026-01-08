# Root-level Dockerfile used by Railway.
# Local Docker Compose still uses backend/Dockerfile with context: ./backend.
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
