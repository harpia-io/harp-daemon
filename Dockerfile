FROM python:3.11.3

WORKDIR /code

RUN apt-get -y install wget
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN echo "ad125f01bada12a1ba2f9986a21c59d2cccbe8d584e7f55079ecbeb7f43a4da4  mariadb_repo_setup" | sha256sum -c -
RUN chmod +x mariadb_repo_setup
RUN ./mariadb_repo_setup --mariadb-server-version="mariadb-10.6"

RUN apt-get update -y
RUN apt-get -y install libmariadb3 libmariadb-dev

COPY requirements.txt requirements.txt
RUN apt-get -y install librdkafka-dev
RUN pip install -r requirements.txt
RUN pip install "uvicorn[standard]" gunicorn==20.1.0
COPY . .
RUN python setup.py install

CMD ["gunicorn", "harp_daemon.__main__:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8081", "--workers", "1", "--threads", "1", "--timeout", "120"]