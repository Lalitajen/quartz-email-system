FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY scripts/ scripts/
COPY templates/ templates/
COPY static/ static/
COPY wsgi.py .

# Copy config template
COPY config/.env.template config/.env.template

# Create directories for runtime
RUN mkdir -p logs attachments

# Render sets PORT dynamically
ENV PORT=5000

EXPOSE ${PORT}

CMD gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 120 wsgi:app
