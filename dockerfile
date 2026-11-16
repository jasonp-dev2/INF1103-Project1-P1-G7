# Expiry & Discount Advisor - runtime image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so this step is cached between code changes
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy the project code (main.py, the four managers, tests/, ...)
COPY . .

# Run as a normal user, with write access to data/ and logs/
RUN useradd --create-home appuser \
    && mkdir -p data logs \
    && chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]