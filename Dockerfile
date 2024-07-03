FROM python:3.12.4

WORKDIR /code

RUN apt-get -y install wget
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN echo "26e5bf36846003c4fe455713777a4e4a613da0df3b7f74b6dad1cb901f324a84  mariadb_repo_setup" | sha256sum -c -
RUN chmod +x mariadb_repo_setup
RUN ./mariadb_repo_setup --mariadb-server-version="mariadb-11.2"

RUN apt-get update -y
RUN apt-get -y install libmariadb3 libmariadb-dev

COPY requirements.txt requirements.txt
RUN apt-get -y install librdkafka-dev
RUN pip install -r requirements.txt
RUN pip install "uvicorn[standard]" gunicorn==22.0.0
COPY . .
RUN python setup.py install

CMD ["gunicorn", "harp_daemon.__main__:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8081", "--workers", "1", "--threads", "4", "--timeout", "120"]