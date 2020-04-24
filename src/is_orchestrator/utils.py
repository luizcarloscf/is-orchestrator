from is_wire.core import Channel, Subscription, Message, Logger
from is_msgs.camera_pb2 import CameraConfig, CameraConfigFields
from is_msgs.common_pb2 import FieldSelector
from google.protobuf.empty_pb2 import Empty
import subprocess
import requests
import socket
import json
import time
import sys
import os

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


def get_metric( name: str,
                prometheus_uri: str = "10.10.2.3:30900",
                timeout: float = 240.0,
                get_every_seconds: float = 2):
    url = "http://{}/api/v1/query?query={}".format(prometheus_uri, name)
    
    start = time.time()

    # simple timeout function
    while True:
        if (time.time() - start) < timeout:
            data = requests.get(url).json()['data']['result']
            if len(data) == 0:
                time.sleep(get_every_seconds)
                continue
            else:
                detect_counter = 0
                for elem in data:
                    detect_counter += float(elem['value'][1])/len(data)
                return detect_counter
        else:
            raise Exception("Timeouted on getting metric!")      


def create_folder(dirname: str,
                  filename: str,
                  log: Logger):

    # Create target directory & all intermediate directories if don't exists
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        log.info("Directory: {} Created", dirname)
    else:
        log.info("Directory: {} already exists", dirname)

    if os.path.isfile('{}/{}'.format(dirname, filename)):
        log.warn(
            "File {} already exists on directory {}.\nWould you like to proceed? All data will be deleted! [y/n]",
            filename, dirname)
        key = input()
        if key == 'y':
            os.remove('{}/{}'.format(dirname, filename))
        elif key == 'n':
            sys.exit(0)
        else:
            log.critical('Invalid command \'{}\', exiting.', key)
            sys.exit(-1)
    else:
        log.info("File not exist")

    with open("{}/{}".format(dirname, filename), "w+") as f:
        f.write('timestamp,fps,uncertainty,pod_skeletons_cpu,pod_skeletons_gpu\n')

def put_data(timestamp: float,
             fps: int,
             uncertainty_filtered: float,
             skeletons_filtered: float,
             pod_skeletons_cpu: int,
             pod_skeletons_gpu: int,
             skeletons_msgs_rate: float,
             dirname: str,
             filename: str):
    with open("{}/{}".format(dirname, filename), "a") as f:
        f.write('{},{},{},{},{},{},{}\n'.format(timestamp,
                                                fps,
                                                uncertainty_filtered,
                                                skeletons_filtered,
                                                skeletons_msgs_rate,
                                                pod_skeletons_cpu,
                                                pod_skeletons_gpu))
