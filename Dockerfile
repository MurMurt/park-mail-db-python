FROM ubuntu:16.04

MAINTAINER Ilnur I. Gataullin

# Обвновление списка пакетов
RUN echo "update start"
RUN apt-get -y update
RUN echo "update end"

#RUN export TZ='Europe/Moscow'
ENV TZ 'Europe/Moscow'
    RUN echo $TZ > /etc/timezone && \
    apt-get update && apt-get install -y tzdata && \
    rm /etc/localtime && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean

# Установка Python3
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install aiohttp
RUN pip3 install asyncpg
RUN pip3 install pyyaml
RUN pip3 install cchardet
RUN pip3 install gunicorn

#
# Установка postgresql
#
RUN apt-get -y update
RUN apt-get -y install wget
RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main' >> /etc/apt/sources.list.d/pgdg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get -y update
ENV PGVER 10
RUN apt-get -y install postgresql-$PGVER




# Run the rest of the commands as the ``postgres`` user created by the ``postgres-$PGVER`` package when it was ``apt-get installed``
USER postgres

COPY DB_API/db/createDB.sql ddl.sql



# Create a PostgreSQL role named ``docker`` with ``docker`` as the password and
# then create a database `docker` owned by the ``docker`` role.
RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER docker WITH SUPERUSER PASSWORD 'docker';" &&\
#    psql --variable=timezone=Eroupe/Moscow &&\
    createdb -O docker docker &&\
    psql -d docker -f ddl.sql &&\
    /etc/init.d/postgresql stop

# Adjust PostgreSQL configuration so that remote connections to the
# database are possible.
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/$PGVER/main/pg_hba.conf

# And add ``listen_addresses`` to ``/etc/postgresql/$PGVER/main/postgresql.conf``
RUN echo "listen_addresses='*'" >> /etc/postgresql/$PGVER/main/postgresql.conf

# Expose the PostgreSQL port
EXPOSE 5432

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Back to the root user
USER root

# Копируем исходный код в Docker-контейнер
ENV WORK /park-mail-db-python/
ADD  DB_API/  $WORK/DB_API/


# Объявлем порт сервера
EXPOSE 5000

#
# Запускаем PostgreSQL и сервер
#
CMD service postgresql start &&\
    cd $WORK/DB_API/server &&\
    gunicorn main:app -c gunicorn.conf.py

