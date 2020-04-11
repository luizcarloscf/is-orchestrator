FROM ubuntu:18.04 as build

RUN apt-get update \
    && apt-get install -y curl ca-certificates

WORKDIR /tmp/
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.14.0/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl                                                                                 

WORKDIR /opt/is
COPY --from=build /tmp/kubectl /usr/local/bin/kubectl
COPY src/ src
COPY setup.py ./
COPY etc/conf/config.json ./

RUN pip3 install .

CMD ["is-orchestrator"]