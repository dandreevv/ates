FROM python:3.11-slim-bookworm

WORKDIR /usr/src/app
COPY . .
RUN pip install -r requirements.txt

ENV PYTHONPATH=/usr/src/app

CMD ["python", "tasks/main.py"]
