
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

ENV APP_HOME=/usr/src/locomotives

# set work directory
WORKDIR $APP_HOME
RUN mkdir $APP_HOME/staticfiles

COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' $APP_HOME/entrypoint.sh
RUN chmod +x $APP_HOME/entrypoint.sh

# copy project
COPY . $APP_HOME

# make app user
RUN groupadd -r app && useradd --no-log-init -r -g app app
RUN chown -R app:app $APP_HOME

# USER app

# run entrypoint.sh
ENTRYPOINT ["/usr/src/locomotives/entrypoint.sh"]

HEALTHCHECK NONE
