from is_wire.core import Channel, Subscription, Message, Logger
from .utils import load_json, get_fps, set_fps, get_metric, k8s_apply, k8s_delete
from .average import MovingAverage
import time
import sys


def main():
    logger = Logger(name="is-orchestrator")

    options_file = sys.argv[1] if len(sys.argv) > 1 else "options.json"
    options = load_json(options_file, logger)

    publish_channel = Channel(options["broker_uri"])
    consumer_channel = Channel(options["broker_uri"])
    subscription = Subscription(consumer_channel)

    average = MovingAverage(length=10)

    while True:
        fps = get_fps(camera=0,
                    publish_channel=publish_channel,
                    consumer_channel=consumer_channel,
                    subscription=subscription,
                    logger=logger)
        if fps is not None:
            break
     
    k8s_apply(name="is-skeletons-detector", file="etc/manifests/is-skeletons-detector-cpu")

    while True:

        skeletons = get_metric(name="skeletons")
        skeletons_average = average.calculate(skeletons)

        info = {
            "skeletons": skeletons,
            "skeletons_average": skeletons_average
        }
        logger.info('{}', str(info).replace("'", '"'))
        time.sleep(2)



if __name__ == '__main__':
    main()
