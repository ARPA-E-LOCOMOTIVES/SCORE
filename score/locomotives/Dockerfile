
FROM python:3.10-slim-bullseye

USER 0

RUN dnf update -y --nodocs && \
    dnf install -y nmap-ncat && \
    dnf clean all && \
    rm -rf /var/cache/dnf

COPY requirements.txt .

RUN pip3.10 install -r requirements.txt

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /usr/src/locomotives

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/locomotives/entrypoint.sh
RUN chmod +x /usr/src/locomotives/entrypoint.sh

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/locomotives/entrypoint.sh"]

HEALTHCHECK NONE
