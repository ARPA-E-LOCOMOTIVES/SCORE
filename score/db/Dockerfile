FROM arl-mmo-containers.artifactory.arl.psu.edu/ironbank/postgres/postgres12:latest

USER root
RUN yum install -y dos2unix

USER postgres
COPY --chown=postgres:postgres docker-entrypoint-initdb.d /docker-entrypoint-initdb.d

WORKDIR /docker-entrypoint-initdb.d

RUN find /docker-entrypoint-initdb.d -type f -print0 | xargs -I '{}' -0 dos2unix '{}'
