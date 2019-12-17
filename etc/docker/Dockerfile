FROM python:3.6-slim as package_step

RUN apt-get update

WORKDIR /opt/is
COPY src/ src
COPY setup.py ./
COPY etc/conf/config.json ./

RUN pip3 install .

# CMD ["is-orchestrator"]