FROM python:3.8-slim

WORKDIR /src

COPY requirements.txt ./requirements.txt
RUN python -m pip install -r requirements.txt

COPY main.py /src/main.py