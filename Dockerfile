FROM python:3.11.3

WORKDIR /code

RUN apt-get -y install wget
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN echo "f5ba8677ad888cf1562df647d3ee843c8c1529ed63a896bede79d01b2ecc3c1d  mariadb_repo_setup" | sha256sum -c -
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