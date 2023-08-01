FROM python:3.11.3

WORKDIR /code

RUN apt-get -y install wget
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN echo "3a562a8861fc6362229314772c33c289d9096bafb0865ba4ea108847b78768d2  mariadb_repo_setup" | sha256sum -c -
RUN chmod +x mariadb_repo_setup
RUN ./mariadb_repo_setup --mariadb-server-version="mariadb-10.9"

RUN apt-get update -y
RUN apt-get -y install libmariadb3 libmariadb-dev

COPY requirements.txt requirements.txt
RUN apt-get -y install librdkafka-dev
RUN pip install -r requirements.txt
RUN pip install "uvicorn[standard]" gunicorn==21.2.0
COPY . .
RUN python setup.py install

CMD ["gunicorn", "harp_daemon.__main__:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8081", "--workers", "1", "--threads", "4", "--timeout", "120"]