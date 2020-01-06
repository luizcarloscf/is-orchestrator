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

def get_metric(logger, service_name):
    prometheus_address = "10.10.2.3:30900"
    url = "http://{}/api/v1/query?query={}".format(prometheus_address,service_name)
    data = requests.get(url).json()['data']['result']
    detect_counter = 0
    for elem in data:
        detect_counter += float(elem['value'][1])/len(data)
    # logger.info("Uncertainty:{}".format(detect_counter))
    return detect_counter

def main():

    logger = Logger(name="is-orchestrator")
    logger.info("Initializing...")
       
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = json.load(open(config_file, 'r'))

    broker_uri = config['broker_uri']
    channel = Channel(broker_uri)
    subscription = Subscription(channel)
    with open("result-02-20-12-2019.txt", "a") as myfile:
        range_cam_services = 4
        for i in range(1,13):
            logger.info("Changing FPS")
            msg_config = CameraConfig()
            msg_config.sampling.frequency.value = i
            for num_svc in range(range_cam_services):
                channel.publish(Message(content=msg_config, reply_to=subscription),topic="CameraGateway.{}.SetConfig".format(num_svc))
                try:
                    reply = channel.consume(timeout=1.0)
                    logger.info('RPC Status: {}',reply.status)
                except socket.timeout: 
                    logger.info('No reply :(')
            for x in range(3):
                time.sleep(5)
                metric = get_metric(logger,"uncertainty")
                logger.info("FPS: {} - Uncertainty:{}",i,metric)
                myfile.write("{},{}\n".format(i,metric))


if __name__ == '__main__':
    main()
