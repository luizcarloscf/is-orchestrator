import re
from kubernetes import client, config

class Pods(object):
    def __init__(self, config_file: str = "/root/.kube/config"):
        config.load_kube_config(config_file=config_file)
        self._v1 = client.CoreV1Api()

    def get_pods(self, namespace: str = "default"):
        ret = self._v1.list_pod_for_all_namespaces(watch=False)
        return [i.metadata.name for i in ret.items]

    def count_pods(self, pod_name: str = "is-skeletons-detector"):
        pods = self.get_pods(namespace="default")
        results = list()
        for pod in pods:
            result = re.match (r"^is-([a-z]+[-]+[a-z]*)", pod)
            results.append(result.group(0))
        return results.count(pod_name)


