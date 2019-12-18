FROM gliderlabs/alpine:3.4 as dl_ikd

RUN apk add --no-cache git && \
git clone https://github.com/luizcarloscf/metrics.git

FROM python:3.6-slim

RUN apt-get update

COPY --from=lachlanevenson/k8s-kubectl:v1.14.0 /usr/local/bin/kubectl /usr/local/bin/kubectl

COPY etc/kube/config /root/.kube/

WORKDIR /opt/is
COPY --from=dl_ikd metrics/is-skeletons-detector/ .
COPY src/ src
COPY setup.py ./
COPY etc/conf/config.json ./

RUN pip3 install .

CMD ["is-orchestrator"]