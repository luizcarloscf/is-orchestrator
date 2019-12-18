FROM python:3.6-slim as package_step

RUN apt-get update && apt-get install -y wget

COPY --from=lachlanevenson/k8s-kubectl:v1.10.3 /usr/local/bin/kubectl /usr/local/bin/kubectl

COPY etc/kube/config /root/.kube/

WORKDIR /opt/is
RUN wget https://raw.githubusercontent.com/luizcarloscf/metrics/master/is-skeletons-detector/is-skeletons-detector-cpu.yaml && \
    wget https://raw.githubusercontent.com/luizcarloscf/metrics/master/is-skeletons-detector/is-skeletons-dectetor-gpu.yaml

COPY src/ src
COPY setup.py ./
COPY etc/conf/config.json ./

RUN pip3 install .

CMD ["is-orchestrator"]