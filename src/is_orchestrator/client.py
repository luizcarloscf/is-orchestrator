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

def has_detection(logger, service_name):
    prometheus_address = "10.10.2.3:30900"
    url = "http://{}/api/v1/query?query={}".format(prometheus_address,service_name)
    data = requests.get(url).json()['data']['result']
    detect_counter = 0
    for elem in data:
        detect_counter += float(elem['value'][1])/len(data)
    logger.info("Incerteza:{}".format(detect_counter))
    return True if detect_counter >= 1.0 else False

def main():

    logger = Logger(name="is-orchestrator")
    logger.info("Initializing...")
       
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = json.load(open(config_file, 'r'))

    broker_uri = config['broker_uri']
    channel = Channel(broker_uri)
    subscription = Subscription(channel)

    range_cam_services = 4
    for i in range(1,12):
        logger.info("FPS = {}",i)
        msg_config = CameraConfig()
        msg_config.sampling.frequency.value = i
        for num_svc in range(range_cam_services):
            channel.publish(Message(content=msg_config, reply_to=subscription),topic="CameraGateway.{}.SetConfig".format(num_svc))
            try:
                reply = channel.consume(timeout=1.0)
                logger.info('RPC Status: {}',reply.status)
            except socket.timeout: 
                logger.info('No reply :(')
        time.sleep(2.5)

if __name__ == '__main__':
    main()
