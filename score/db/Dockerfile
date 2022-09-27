FROM postgres:12-bullseye

USER root
RUN apt update -y && \
#     apt install -y dos2unix && \
    apt clean && \
    rm -rf /var/cache/apt

# COPY ./docker-entrypoint-initdb.d/ /docker-entrypoint-initdb.d/
USER postgres
COPY --chown=postgres:postgres docker-entrypoint-initdb.d /docker-entrypoint-initdb.d

WORKDIR /docker-entrypoint-initdb.d

# RUN find /docker-entrypoint-initdb.d -type f -print0 | xargs -I '{}' -0 dos2unix '{}'
