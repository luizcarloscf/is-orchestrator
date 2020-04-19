from is_wire.core import Channel, Subscription, Message, Logger
from utils import load_json, get_fps, set_fps, get_metric, k8s_apply, k8s_delete, create_folder, put_data
from average import MovingAverage
from pods import Pods
import time
import sys
import json


def main():

    high_processing = False
    uncertainty = 0.0
    uncertainty_average = 0.0
    skeletons_pods_cpu = 0
    skeletons_pods_gpu = 0
    fps = 0

    logger = Logger(name="is-orchestrator")

    grouper_configmap = load_json(file_name="etc/conf/configmap-grouper.json", log=logger)
    grouper_options = load_json(file_name="etc/conf/options-grouper.json", log=logger)

    options_file = sys.argv[1] if len(sys.argv) > 1 else "etc/conf/options.json"
    options = load_json(options_file, logger)

    create_folder(filename=options['file_name'], dirname=options['folder'], log=logger)

    publish_channel = Channel(options["broker_uri"])
    consumer_channel = Channel(options["broker_uri"])
    subscription = Subscription(consumer_channel)

    average_sks = MovingAverage(length=10)
    average_unc = MovingAverage(length=10)

    pods = Pods(config_file=options['config_file'])

    # waiting for a response of the cameras
    while True:
        fps = get_fps(camera=0,
                    publish_channel=publish_channel,
                    consumer_channel=consumer_channel,
                    subscription=subscription,
                    logger=logger)
        if fps is not None:
            break
    
    # setting initial condition
    fps = options['fps']['min']
    set_fps(fps=fps,
            camera=0,
            consumer_channel=consumer_channel,
            publish_channel=publish_channel,
            subscription=subscription,
            logger=logger)
    k8s_apply(name="is-skeletons-detector",
              filename="etc/manifests/is-skeletons-detector-cpu")
    time.sleep(120)
    last_change = time.time()
    start_time = time.time()

    while True:
        
        # number of skeletons
        skeletons = get_metric(name="skeletons", prometheus_uri=options['prometheus_uri'])
        
        # number of skeletons on a moving average
        skeletons_average = average_sks.calculate(skeletons)

        if high_processing is False and skeletons_average <= 1:
            uncertainty = 0
            uncertainty_average = average_unc.calculate(uncertainty)
            pass
        
        elif high_processing is False and skeletons_average >= 1:
            high_processing = True

            k8s_delete(name="is-skeletons-detector",
                       filename="etc/manifests/is-skeletons-detector-cpu")
            logger.info("is-skeletons-detector-cpu deleted")

            k8s_apply(name="is-skeletons-detector",
                      filename="etc/manifests/is-skeletons-detector-gpu")
            logger.info("is-skeletons-detector-gpu created")

            k8s_apply(name="is-skeletons-grouper",
                      filename="etc/manifests/is-skeletons-grouper")
            logger.info("is-skeletons-grouper created")

            k8s_apply(name="is-gesture-recognizer",
                      filename="etc/manifests/is-gesture-recognizer")
            logger.info("is-gesture-recognizer created")
            
            time.sleep(120)
            last_change = time.time()
            continue

        elif high_processing is True and skeletons_average >= 1:

            uncertainty = get_metric(name="uncertainty_total", prometheus_uri=options['prometheus_uri'])
            uncertainty_average = average_unc.calculate(uncertainty)
            dt = time.time() - last_change
            if uncertainty_average >= options['uncertainty_threshold'] and fps < options['fps']['max'] and dt > options['minimal_time']:

                # increase FPS
                fps += 1
                set_fps(fps=fps,
                        camera=0,
                        consumer_channel=consumer_channel,
                        publish_channel=publish_channel,
                        subscription=subscription,
                        logger=logger)
                
                # edit is-skeletons-grouper configmap
                grouper_options["period_ms"] = int((1 / fps) * 1000)
                grouper_configmap["data"]["grouper_0"] = json.dumps(grouper_options)
                with open('./etc/conf/configmap-grouper.json', 'w') as f:
                    json.dump(grouper_configmap, f, ensure_ascii=False, indent=4)

                # apply new is-skeletons-grouper configmap
                k8s_apply(name="configmap-grouper", filename="etc/conf/configmap-grouper.json")
                # renew deployment of is-skeletons-grouper
                k8s_delete(name="is-skeletons-grouper", filename="etc/manifests/is-skeletons-grouper/deployment.yaml")
                k8s_apply(name="is-skeletons-grouper", filename="etc/manifests/is-skeletons-grouper/deployment.yaml")
                logger.info("Deployment is-skeletons-grouper edited!")
                last_change = time.time()
                continue

        
        elif high_processing is True and skeletons_average < 0.5:
            high_processing = False
            uncertainty = 0
            uncertainty_average = average_unc.calculate(uncertainty)

            k8s_delete(name="is-skeletons-detector",
                       filename="etc/manifests/is-skeletons-detector-gpu")
            logger.info("deployment is-skeletons-detector-gpu deleted")

            k8s_delete(name="is-skeletons-grouper",
                       filename="etc/manifests/is-skeletons-grouper")
            logger.info("deployment is-skeletons-grouper deleted")

            k8s_delete(name="is-gesture-recognizer",
                       filename="etc/manifests/is-gesture-recognizer")
            logger.info("deployment is-gesture-recognizer deleted")

            k8s_apply(name="is-skeletons-detector",
                      filename="etc/manifests/is-skeletons-detector-cpu")
            logger.info("deployment is-skeletons-detector-cpu created")
            continue
        # number of skeletons pods
        skeletons_pods_cpu = pods.count_pods(pod_name="is-skeletons-cpu")
        skeletons_pods_gpu = pods.count_pods(pod_name="is-skeletons-detector")

        put_data(timestamp=(time.time() - start_time),
                 fps=fps,
                 uncertainty=uncertainty_average,
                 pod_skeletons_cpu=skeletons_pods_cpu,
                 pod_skeletons_gpu=skeletons_pods_gpu,
                 dirname=options["folder"],
                 filename=options["file_name"])

        info = {
            "fps": fps,
            "uncertainty": uncertainty,
            "uncertainty_average": uncertainty_average,
            "skeletons": skeletons,
            "skeletons_average": skeletons_average,
            "skeletons_pods_cpu": skeletons_pods_cpu,
            "skeletons_pods_gpu": skeletons_pods_gpu
        }
        logger.info('{}', str(info).replace("'", '"'))
        time.sleep(5)



if __name__ == '__main__':
    main()
