import re
from is_wire.core import Logger
from kubernetes import client, config

class Pods(object):
    def __init__(self, config_file: str = "/root/.kube/config"):
        config.load_kube_config(config_file=config_file)
        self._v1 = client.CoreV1Api()

    def get_pods(self, namespace: str = "default"):

        ret = self._v1.list_pod_for_all_namespaces(watch=False)
        return [i.metadata.name for i in ret.items if i.metadata.namespace == namespace]

    def count_pods(self,
                   pod_name: str = "is-skeletons-detector",
                   regex_match: str = "^is-([a-z]+[-]+[a-z]*)"):

        pods = self.get_pods(namespace="default")
        results = list()
        for pod in pods:
            result = re.match (r"{}".format(regex_match), pod)
            if result is not None:
                results.append(result.group(0))
        return results.count(pod_name)
