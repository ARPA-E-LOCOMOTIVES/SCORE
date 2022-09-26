ARG BASE_REGISTRY=registry1.dso.mil
ARG BASE_IMAGE=ironbank/opensource/python
ARG BASE_TAG=v3.10

FROM ${BASE_REGISTRY}/${BASE_IMAGE}:${BASE_TAG}

USER 0

COPY yum.repos.d/ /etc/yum.repos.d
# COPY banner/issue /etc/
COPY cacerts/ /etc/pki/ca-trust/source/anchors

RUN /bin/update-ca-trust && \
    rm -f /etc/yum.repos.d/ironbank.repo && \
    sed -i "s/enabled=1/enabled=0/" /etc/dnf/plugins/subscription-manager.conf

RUN dnf update -y --nodocs && \
    dnf install -y nmap-ncat && \
    dnf clean all && \
    rm -rf /var/cache/dnf

COPY requirements.txt .
# an internal ARL thing
RUN pip3.10 config set global.index-url https://artifactory.arl.psu.edu/artifactory/api/pypi/pypi/simple
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
