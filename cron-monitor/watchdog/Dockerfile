FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY watchdog.py .
USER 65534:65534
CMD ["python", "-u", "watchdog.py"]
