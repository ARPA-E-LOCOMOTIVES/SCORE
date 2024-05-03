FROM quay.io/jupyter/scipy-notebook

USER root

RUN chown -R ${NB_UID} ${HOME}

## ARL steps for conda install

# COPY ./.condarc /opt/conda

## Switch to the lowly user, no more root.
USER ${NB_USER}
WORKDIR ${HOME}

RUN conda init && \ 
    conda install \
        gdal \
        geopandas \
        folium \
        osmnx \
        pip \
        python=3.11 && \
    conda clean --all --yes
