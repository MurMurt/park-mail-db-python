FROM ubuntu:18.04

MAINTAINER Ilnur I. Gataullin

# Обвновление списка пакетов
RUN echo "update start"
RUN apt-get -y update
RUN echo "update end"

#
# Установка postgresql
#
ENV PGVER 10
RUN apt-get install -y postgresql-$PGVER

# Run the rest of the commands as the ``postgres`` user created by the ``postgres-$PGVER`` package when it was ``apt-get installed``
USER postgres

COPY db/createDB.sql ddl.sql


# Create a PostgreSQL role named ``docker`` with ``docker`` as the password and
# then create a database `docker` owned by the ``docker`` role.
RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER docker WITH SUPERUSER PASSWORD 'docker';" &&\
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


# Объявлем порт сервера
EXPOSE 5000

#
# Запускаем PostgreSQL и сервер
#
CMD service postgresql start
#&& hello-server --scheme=http --port=5000 --host=0.0.0.0 --database=postgres://docker:docker@localhost/docker