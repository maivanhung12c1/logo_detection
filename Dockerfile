# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster
RUN mkdir /app
ADD . /app
WORKDIR /app
RUN pip3 install opencv-python-headless==4.5.3.56
RUN pip install -r requirements.txt
CMD ["python", "app.py"]