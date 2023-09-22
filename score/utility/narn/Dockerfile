FROM jupyter/scipy-notebook

USER root

RUN chown -R ${NB_UID} ${HOME}

## Switch to the lowly user, no more root.
USER ${NB_USER}
WORKDIR ${HOME}

RUN conda init && \ 
    conda install \
        gdal \
        geopandas \
        osmnx \
        pip \
        python=3.11 && \
    conda clean --all --yes
