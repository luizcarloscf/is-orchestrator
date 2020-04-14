from is_wire.core import Channel, Subscription, Message, Logger
from is_msgs.camera_pb2 import CameraConfig, CameraConfigFields
from is_msgs.common_pb2 import FieldSelector
from google.protobuf.empty_pb2 import Empty
import subprocess
import requests
import socket
import json
import time

def load_json(file_name: str,
              log: Logger):
    try:
        with open(file_name, 'r') as f:
            try:
                op = json.load(f)
                log.info('Loaded options: \n{}', op)
                return op
            except Exception as ex:
                log.critical('Unable to load options from \'{}\'. \n{}', file_name, ex)
    except Exception:
        log.critical('Unable to open file \'{}\'', file_name)

def get_fps(camera: int,
            publish_channel: Channel,
            consumer_channel: Channel,
            subscription: Subscription,
            logger: Logger,
            timeout: float = 5.0):

    selector = FieldSelector(fields=[CameraConfigFields.Value("SAMPLING_SETTINGS")])
    publish_channel.publish(
            Message(content=selector, reply_to=subscription),
            topic="CameraGateway.{}.GetConfig".format(camera))
    current_fps = None
    try:
        reply = consumer_channel.consume(timeout=timeout)
        unpacked_msg = reply.unpack(CameraConfig)
        current_fps = unpacked_msg.sampling.frequency.value
        logger.info("Camera: {}, FPS: {}".format(camera, current_fps))
    except socket.timeout:
        logger.info('No reply from camera {}', camera)
    
    return current_fps

def set_fps(fps: float,
            camera: int,
            publish_channel: Channel,
            consumer_channel: Channel,
            subscription: Subscription,
            logger: Logger,
            timeout: float = 5.0):

    msg_config = CameraConfig()
    msg_config.sampling.frequency.value = fps
    publish_channel.publish(
            Message(content=msg_config, reply_to=subscription),
            topic="CameraGateway.{}.SetConfig".format(camera))
    try:
        reply = consumer_channel.consume(timeout=timeout)
        logger.info('Change FPS of camera {}, RPC Status: {}', camera, reply.status)
    except socket.timeout:
        logger.critical('No reply from camera {}', camera)


def get_metric(name: str,
               prometheus_uri: str = "10.10.2.3:30900"):
    url = "http://{}/api/v1/query?query={}".format(prometheus_uri, name)
    data = requests.get(url).json()['data']['result']
    detect_counter = 0
    for elem in data:
        detect_counter += float(elem['value'][1])/len(data)
    return detect_counter

def k8s_apply(name: str,
              filename: str):
    kubectl_command = '/usr/bin/kubectl apply -f {} > /dev/null 2>&1'.format(filename)
    subprocess.call(['bash', '-c', kubectl_command])
    time.sleep(5)
    

def k8s_delete(name: str,
               filename: str):
    kubectl_command = '/usr/bin/kubectl delete -f {}'.format(filename)
    subprocess.call(['bash', '-c', kubectl_command, '> /dev/null 2>&1'])
    time.sleep(5)