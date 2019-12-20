from is_wire.core import Channel, Subscription, Message, Logger
from is_msgs.image_pb2 import ObjectAnnotations
from google.protobuf.empty_pb2 import Empty
from is_msgs.camera_pb2 import CameraConfig, CameraConfigFields
from is_msgs.common_pb2 import FieldSelector
from enum import Enum
import requests
import json
import socket
import sys
import os
import time

class k8s_control(Enum):
    apply = (1,'apply -f')
    delete_deploy = (2,'delete deploy')
    delete_pods = (3,'delete pods')
    get_pods = (4,'get pods')

    def __str__(self):
        return self.value[1]

def has_detection(logger, service_name):
    prometheus_address = "10.10.2.3:30900"
    url = "http://{}/api/v1/query?query={}".format(prometheus_address,service_name)
    data = requests.get(url).json()['data']['result']
    detect_counter = 0
    for elem in data:
        detect_counter += float(elem['value'][1])/len(data)
    logger.info("Detection Average:{}".format(detect_counter))
    return True if detect_counter >= 1.0 else False

def kubernetes_control(logger=None,options=None,arg=None):
    cmd = "kubectl {} {}".format(options,arg) if arg is not None else "kubectl {}".format(options)
    os.system(cmd) 


def main():

    logger = Logger(name="is-orchestrator")
    logger.info("Initializing...")
    cpu_deployment_name = 'is-skeletons-detector-cpu'
    gpu_deployment_name = 'is-skeletons-detector-gpu'

    cpu_deployment_address = 'is-skeletons-detector-cpu.yaml'
    gpu_deployment_address = 'is-skeletons-detector-gpu.yaml'
       
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = json.load(open(config_file, 'r'))

    broker_uri = config['broker_uri']
    pub_channel = Channel(broker_uri)
    con_channel = Channel(broker_uri)
    subscription = Subscription(con_channel)

    logger.info("Creating CPU deployment")
    kubernetes_control(logger,k8s_control.apply,cpu_deployment_address)
    last_change = time.time()
    
    selector = FieldSelector(fields=[CameraConfigFields.Value("SAMPLING_SETTINGS")])
    current_fps = 0
    while current_fps == 0:
        pub_channel.publish(
            Message(content=selector, reply_to=subscription),
            topic="CameraGateway.0.GetConfig")
        try:
            reply = con_channel.consume(timeout=5.0)
            unpacked_msg = reply.unpack(CameraConfig)
            current_fps = unpacked_msg.sampling.frequency.value
            logger.info("Current FPS: {}".format(current_fps))
        except socket.timeout:
            logger.info('No reply :(')

    range_cam_services = 4
    while True:
        service_name = "skeletons_detected"
        maybe_detect = has_detection(logger,service_name)
        maybe_change = True if (time.time() - last_change) > 30 else False
        if maybe_detect and current_fps != 10.0 and maybe_change:
            logger.info("DETECTED! Changing FPS to 10.0")
            current_fps = 10.0
            msg_config = CameraConfig()
            msg_config.sampling.frequency.value = 10
            for num_svc in range(range_cam_services):
                pub_channel.publish(Message(content=msg_config, reply_to=subscription),topic="CameraGateway.{}.SetConfig".format(num_svc))
                try:
                    reply = con_channel.consume(timeout=1.0)
                    logger.info('RPC Status: {}',reply.status)
                except socket.timeout: 
                    logger.info('No reply :(')
            logger.info("DETECTED! Deleting CPU deployment")
            kubernetes_control(logger,k8s_control.delete_deploy,cpu_deployment_name)
            logger.info("DETECTED! Creating GPU deployment")
            kubernetes_control(logger,k8s_control.apply,gpu_deployment_address)
            last_change = time.time()
        elif not maybe_detect and current_fps != 1.0 and maybe_change:
            logger.info("NOT DETECTED! Changing FPS to 1.0")
            current_fps = 1.0
            msg_config = CameraConfig()
            msg_config.sampling.frequency.value = 1
            for num_svc in range(range_cam_services):
                pub_channel.publish(Message(content=msg_config, reply_to=subscription),topic="CameraGateway.{}.SetConfig".format(num_svc))
                try:
                    reply = con_channel.consume(timeout=1.0)
                    logger.info('RPC Status: {}',reply.status)
                except socket.timeout: 
                    logger.info('No reply :(')
            logger.info("NOT DETECTED! Deleting GPU deployment")
            kubernetes_control(logger,k8s_control.delete_deploy,gpu_deployment_name)
            logger.info("NOT DETECTED! Creating CPU deployment")
            kubernetes_control(logger,k8s_control.apply,cpu_deployment_address)
            last_change = time.time()
        time.sleep(2.5)

if __name__ == '__main__':
    main()
