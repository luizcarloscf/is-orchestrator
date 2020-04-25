FROM ubuntu:18.04 as build

RUN apt-get update                                                       \
    && apt-get install -y curl ca-certificates python3 python3-distutils

WORKDIR /tmp/
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.14.0/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl                                                                              \
    && mv ./kubectl /usr/bin/kubectl                                                                                 

WORKDIR /tmp/
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
  && python3 get-pip.py                                     \
  && rm -f get-pip.py

WORKDIR /opt/is
COPY src/ src
COPY setup.py ./
COPY etc/conf/ ./etc/conf
COPY etc/manifests ./etc/manifests 
COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

CMD ["is-orchestrator"]
