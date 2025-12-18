FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Create directory for SQLite database
RUN mkdir -p /app/data

EXPOSE 5000

ENV PORT=5000

CMD ["python", "main.py"]
