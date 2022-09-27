
FROM python:3.10-slim-bullseye

USER 0

RUN apt update -y  && \
    apt install -y ncat && \
    apt clean && \
    rm -rf /var/cache/apt

# set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /usr/src/locomotives

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//g' /entrypoint.sh
RUN chmod +x /entrypoint.sh

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

HEALTHCHECK NONE
