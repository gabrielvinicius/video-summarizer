FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Uvicorn será usado no comando
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
