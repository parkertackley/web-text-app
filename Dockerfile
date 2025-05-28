FROM python:3.8.2

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 8080

ENV FLASK_APP=server.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run", "--port=8080"]
