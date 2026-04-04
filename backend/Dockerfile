FROM python:3.12-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY agent ./agent

EXPOSE 8000

# Fixed port so split platforms (e.g. Railway private DNS) can use api.railway.internal:8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
