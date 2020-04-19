import time
import json
import subprocess
from is_wire.core import Logger

class Orchestrator(object):
    def __init__(self, 
                 grouper_configmap: dict,
                 grouper_options: dict,
                 log: Logger,
                 waiting_time: float = 150,
                 grouper_configmap_file: str = "etc/conf/configmap-grouper.json",
                 skeletons_cpu_folder: str = "etc/manifests/is-skeletons-detector-cpu",
                 skeletons_gpu_folder: str = "etc/manifests/is-skeletons-detector-gpu",
                 skeletons_grouper_folder: str = "etc/manifests/is-skeletons-grouper",
                 gesture_recognizer_folder: str = "etc/manifests/is-gesture-recognizer"):

        self._waiting_time = waiting_time
        self._skeletons_cpu_folder = skeletons_cpu_folder
        self._skeletons_gpu_folder = skeletons_gpu_folder
        self._skeletons_grouper_folder = skeletons_grouper_folder
        self._gesture_recognizer_folder = gesture_recognizer_folder
        self._grouper_configmap = grouper_configmap
        self._grouper_options = grouper_options
        self._grouper_configmap_file = grouper_configmap_file
        self._log = log
        self._apply(name="is-skeletons-detector-cpu",
                   file_name=self._skeletons_cpu_folder)
        self._wait(seconds=self._waiting_time)

    def _apply(self, name, file_name):
        kubectl_command = '/usr/bin/kubectl apply -f {} > /dev/null 2>&1'.format(file_name)
        subprocess.call(['bash', '-c', kubectl_command])
        info = {
            "service_name" : name,
            "file_name": file_name 
        }
        self._log.info('{}', str(info).replace("'", '"'))
    
    def _delete(self, name, file_name):
        kubectl_command = '/usr/bin/kubectl apply -f {} > /dev/null 2>&1'.format(file_name)
        subprocess.call(['bash', '-c', kubectl_command])
        info = {
            "service_name" : name,
            "file_name": file_name 
        }
        self._log.info('{}', str(info).replace("'", '"'))
    
    def _wait(self, seconds):
        info = {
            "waiting" : seconds,
        }
        self._log.info('{}', str(info).replace("'", '"'))
        time.sleep(seconds)

    def fast_processing(self):
        self._delete(name="is-skeletons-detector-cpu",
                    file_name=self._skeletons_cpu_folder)
        self._apply(name="is-skeletons-detector-gpu",
                   file_name=self._skeletons_gpu_folder)
        self._apply(name="is-skeletons-grouper",
                   file_name=self._skeletons_grouper_folder)
        self._apply(name="is-gesture-recognizer",
                   file_name=self._gesture_recognizer_folder)
        self._wait(seconds=self._waiting_time)
    
    def slow_processing(self):
        self._delete(name="is-skeletons-detector-gpu",
                   file_name=self._skeletons_gpu_folder)
        self._delete(name="is-skeletons-grouper",
                   file_name=self._skeletons_grouper_folder)
        self._delete(name="is-gesture-recognizer",
                   file_name=self._gesture_recognizer_folder)
        self._apply(name="is-skeletons-detector-cpu",
                    file_name=self._skeletons_cpu_folder)
        self._wait(seconds=self._waiting_time)
    
    def edit_grouper(self,
                     fps: float):
        self._grouper_options["period_ms"] = int((1 / fps) * 1000)
        self._grouper_configmap["data"]["grouper_0"] = json.dumps(self._grouper_options)
        with open(self._grouper_configmap_file, 'w') as f:
            json.dump(self._grouper_configmap, f, ensure_ascii=False, indent=4)

        # apply new is-skeletons-grouper configmap
        self._apply(name="configmap-grouper", file_name=self._grouper_configmap_file)
        
        # renew deployment of is-skeletons-grouper
        self._delete(name="is-skeletons-grouper", file_name="{}/deployment.yaml".format(self._skeletons_grouper_folder))
        self._apply(name="is-skeletons-grouper", file_name="{}/deployment.yaml".format(self._skeletons_grouper_folder))

        self._wait(seconds=(self._waiting_time/3))