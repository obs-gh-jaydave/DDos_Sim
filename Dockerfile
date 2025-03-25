FROM python:3.10-slim

WORKDIR /app

COPY ddos_runner.py .

RUN pip install requests

CMD ["python", "ddos_runner.py"]