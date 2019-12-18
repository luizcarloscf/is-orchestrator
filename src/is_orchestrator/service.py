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

def kubernetes_control(option,arg=None):
    os.system("kubectl {} {}".format(option,arg)) if arg is not None else os.system("kubectl {}".format(option))


def main():

    logger = Logger(name="is-orchestrator")
    cpu_deployment_name = 'is-skeletons-detector-cpu'
    gpu_deployment_name = 'is-skeletons-detector-gpu'

    cpu_deployment_address = 'is-skeletons-detector-cpu.yaml'
    gpu_deployment_address = 'is-skeletons-dectetor-gpu.yaml'
       
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = json.load(open(config_file, 'r'))

    broker_uri = config['broker_uri']
    channel = Channel(broker_uri)
    subscription = Subscription(channel)

    selector = FieldSelector(fields=[CameraConfigFields.Value("SAMPLING_SETTINGS")])
    channel.publish(
        Message(content=selector, reply_to=subscription),
        topic="CameraGateway.0.GetConfig")
    try:
        reply = channel.consume(timeout=1.0)
        unpacked_msg = reply.unpack(CameraConfig)
        current_fps = unpacked_msg.sampling.frequency.value
        logger.info("Current FPS: {}".format(current_fps))
    except socket.timeout:
        logger.info('No reply :(')

    range_cam_services = 4
    while True:
        service_name = "skeletons_detected"
        if has_detection(logger,service_name) and current_fps != 10.0:
            logger.info("DETECTED! Changing FPS to 10.0")
            current_fps = 10.0
            msg_config = CameraConfig()
            msg_config.sampling.frequency.value = 10
            for num_svc in range(range_cam_services):
                channel.publish(Message(content=msg_config, reply_to=subscription),topic="CameraGateway.{}.SetConfig".format(num_svc))
                try:
                    reply = channel.consume(timeout=1.0)
                    logger.info('RPC Status: {}',reply.status)
                except socket.timeout: 
                    logger('No reply :(')
            logger.info("DETECTED! Deleting CPU deployment")
            kubernetes_control(k8s_control.delete_deploy,cpu_deployment_name)
            logger.info("DETECTED! Creating GPU deployment")
            kubernetes_control(k8s_control.apply,gpu_deployment_address)
        elif not has_detection(logger,service_name) and current_fps != 1.0:
            logger.info("NOT DETECTED! Changing FPS to 1.0")
            current_fps = 1.0
            msg_config = CameraConfig()
            msg_config.sampling.frequency.value = 1
            for num_svc in range(range_cam_services):
                channel.publish(Message(content=msg_config, reply_to=subscription),topic="CameraGateway.{}.SetConfig".format(num_svc))
                try:
                    reply = channel.consume(timeout=1.0)
                    logger.info('RPC Status: {}',reply.status)
                except socket.timeout: 
                    logger.info('No reply :(')
            logger.info("NOT DETECTED! Deleting GPU deployment")
            kubernetes_control(k8s_control.delete_deploy,gpu_deployment_name)
            logger.info("NOT DETECTED! Creating CPU deployment")
            kubernetes_control(k8s_control.apply,cpu_deployment_address)
        time.sleep(2.5)

if __name__ == '__main__':
    main()
