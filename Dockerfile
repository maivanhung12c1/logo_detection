# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip
# RUN pip install opencv-python-headless==4.5.3.56
RUN apt-get update && apt-get install -y python3-opencv
RUN pip install opencv-python
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "app.py", "--host=0.0.0.0"]