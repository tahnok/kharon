FROM python:3.11-slim

RUN pip install poetry  
RUN mkdir -p /app  
COPY . /app

WORKDIR /app

ENV PYTHONUNBUFFERED=1
RUN poetry install
CMD ["poetry", "run", "python", "kharon.py"]

