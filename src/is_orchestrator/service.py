from is_wire.core import Channel, Subscription, Message, Logger
from .utils import load_json, get_fps, set_fps, get_metric, k8s_apply, k8s_delete
from .average import MovingAverage
from .pods import Pods
import time
import sys
import json


def main():

    logger = Logger(name="is-orchestrator")

    grouper_configmap = load_json(file_name="etc/conf/configmap-grouper.json", log=logger)
    grouper_options = load_json(file_name="etc/conf/options-grouper.json", log=logger)

    options_file = sys.argv[1] if len(sys.argv) > 1 else "etc/conf/options.json"
    options = load_json(options_file, logger)

    publish_channel = Channel(options["broker_uri"])
    consumer_channel = Channel(options["broker_uri"])
    subscription = Subscription(consumer_channel)

    average_sks = MovingAverage(length=10)
    average_unc = MovingAverage(length=10)

    pods = Pods(config_file="/root/.kube/config")

    while True:
        fps = get_fps(camera=0,
                    publish_channel=publish_channel,
                    consumer_channel=consumer_channel,
                    subscription=subscription,
                    logger=logger)
        if fps is not None:
            break

    fps = 1
    set_fps(fps=fps,
            camera=0,
            consumer_channel=consumer_channel,
            publish_channel=publish_channel,
            subscription=subscription,
            logger=logger)
    last_change = time.time()


    k8s_apply(name="is-skeletons-detector",
              filename="etc/manifests/is-skeletons-detector-cpu")
    
    high_processing = False

    while True:

        skeletons = get_metric(name="skeletons")
        skeletons_average = average_sks.calculate(skeletons)
        skeletos_pods = pods.count_pods(pod_name="is-skeletons-detector")

        if high_processing is False and skeletons_average <= 1:
            pass
        
        elif high_processing is False and skeletons_average >= 1:
            high_processing = True
            k8s_delete(name="is-skeletons-detector",
                       filename="etc/manifests/is-skeletons-detector-cpu")
            k8s_apply(name="is-skeletons-detector",
                      filename="etc/manifests/is-skeletons-detector-gpu")
            k8s_apply(name="is-skeletons-grouper",
                      filename="etc/manifests/is-skeletons-grouper")
            k8s_apply(name="is-gesture-recognizer",
                      filename="etc/manifests/is-gesture-recognizer")
            last_change = time.time()

        elif high_processing is True and skeletons_average >= 1:

            uncertainty = get_metric(name="uncertainty")
            uncertainty_average = average_unc.calculate(uncertainty)
            
            dt = time.time() - last_change

            if uncertainty_average >= 1 and fps < 10 and dt > 60:

                last_change = time.time()
                fps += 1
                set_fps(fps=fps,
                        camera=0,
                        consumer_channel=consumer_channel,
                        publish_channel=publish_channel,
                        subscription=subscription,
                        logger=logger)

                grouper_options["period_ms"] = int((1 / fps) * 1000)
                grouper_configmap["data"]["grouper_0"] = json.dumps(options)
                with open('./etc/conf/configmap-grouper.json', 'w') as f:
                    json.dump(grouper_configmap, f, ensure_ascii=False, indent=4)

                k8s_apply(name="configmap-grouper", filename="etc/conf/configmap-grouper.json")
                k8s_delete(name="is-skeletons-grouper", filename="etc/manifests/is-skeletons-grouper/deploy.yaml")
                k8s_apply(name="is-skeletons-grouper", filename="etc/manifests/is-skeletons-grouper/deploy.yaml")

        
        elif high_processing is True and skeletons_average <= 1:
            high_processing = False
            k8s_delete(name="is-skeletons-detector",
                       filename="etc/manifests/is-skeletons-detector-gpu")
            k8s_delete(name="is-skeletons-grouper",
                       filename="etc/manifests/is-skeletons-grouper")
            k8s_delete(name="is-gesture-recognizer",
                       filename="etc/manifests/is-gesture-recognizer")
            k8s_apply(name="is-skeletons-detector",
                      filename="etc/manifests/is-skeletons-detector-cpu")


        info = {
            "skeletons": skeletons,
            "skeletons_average": skeletons_average,
            "skeletons_pods": skeletos_pods
        }
        logger.info('{}', str(info).replace("'", '"'))
        time.sleep(2)



if __name__ == '__main__':
    main()
