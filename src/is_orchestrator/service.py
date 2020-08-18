from is_wire.core import Channel, Subscription, Message, Logger
from utils import load_json, get_fps, set_fps, get_metric, create_folder, put_data
from orchestrator import Orchestrator
from average import MovingAverage
from pods import Pods
import time
import sys
import json


def main():
 
    logger = Logger(name="is-orchestrator")

    grouper_configmap = load_json(file_name="etc/conf/configmap-grouper.json",
                                  log=logger,
                                  show=False)
    grouper_options = load_json(file_name="etc/conf/options-grouper.json",
                                log=logger,
                                show=False)
    options_file = sys.argv[1] if len(sys.argv) > 1 else "etc/conf/options.json"
    options = load_json(file_name=options_file,
                        log=logger,
                        show=True)

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
    orchestrator = Orchestrator(grouper_configmap=grouper_configmap,
                                grouper_options=grouper_options,
                                grouper_configmap_file="etc/conf/configmap-grouper.json",
                                log=logger,
                                waiting_time=options['waiting_time'],
                                skeletons_cpu_folder=options['skeletons_detector_cpu_folder'],
                                skeletons_gpu_folder=options['skeletons_detector_gpu_folder'],
                                skeletons_grouper_folder=options['skeletons_grouper_folder'],
                                gesture_recognizer_folder=options['gesture_recognizer_folder'])
    
   
    skeletons = get_metric(name="skeletons", prometheus_uri=options['prometheus_uri'])

    filter_by = '{namespace!="",queue="SkeletonsDetector.Detection"}'
    msgs_rate_skeletons = get_metric(name='rate(rabbitmq_queue_messages_published_total'
                                            + filter_by + '[1m])'
                                            + '/rabbitmq_queue_consumers'
                                            + filter_by,
                                     prometheus_uri=options['prometheus_uri'])

    fast_processing = False
    uncertainty = 0.0
    last_change = time.time()
    start_time = time.time() 
    
    while True:
        
        msgs_rate_skeletons = get_metric(name='rate(rabbitmq_queue_messages_published_total'
                                            + filter_by + '[1m])'
                                            + '/rabbitmq_queue_consumers'
                                            + filter_by,
                                         prometheus_uri=options['prometheus_uri'])
       
       
      
        skeletons = get_metric(name="skeletons", prometheus_uri=options['prometheus_uri'])
        
        
        skeletons_average = average_sks.calculate(skeletons)

        if fast_processing is False and skeletons_average < options['skeletons']:
            uncertainty_average = average_unc.calculate(uncertainty)
        
        elif fast_processing is False and skeletons_average >= 1:
            fast_processing = True
            orchestrator.fast_processing()
            
            skeletons = get_metric(name="skeletons", prometheus_uri=options['prometheus_uri'])
            uncertainty = get_metric(name="uncertainty_total", prometheus_uri=options['prometheus_uri'])
            
            last_change = time.time()
            continue

        elif fast_processing is True and skeletons_average > (options['skeletons'] - options['tolerance']):
            uncertainty = get_metric(name="uncertainty_total", prometheus_uri=options['prometheus_uri'])
            
            uncertainty_average = average_unc.calculate(uncertainty)
            dt = time.time() - last_change

            if fps < options['fps']['max'] and dt > options['last_change_time']:
                fps += 1
                set_fps(fps=fps,
                        camera=0,
                        consumer_channel=consumer_channel,
                        publish_channel=publish_channel,
                        subscription=subscription,
                        logger=logger)
                orchestrator.edit_grouper(fps=fps)
                last_change = time.time()
                continue

        
        elif fast_processing is True and skeletons_average <= (options['skeletons'] - options['tolerance']):
            orchestrator.slow_processing()
            skeletons = get_metric(name="skeletons", prometheus_uri=options['prometheus_uri'])
            fps = 1
            set_fps(fps=fps,
                    camera=0,
                    consumer_channel=consumer_channel,
                    publish_channel=publish_channel,
                    subscription=subscription,
                    logger=logger)

            fast_processing = False
            uncertainty = 0.0
            last_change = time.time()
            continue

        skeletons_pods_cpu = pods.count_pods(pod_name="is-skeletons-cpu", namespace="orchestrator", regex_match=options["regex_match"])
        skeletons_pods_gpu = pods.count_pods(pod_name="is-skeletons-detector", namespace="orchestrator", regex_match=options["regex_match"])
        
        put_data(timestamp=(time.time() - start_time),
                 fps=fps,
                 uncertainty=uncertainty,
                 uncertainty_filtered=uncertainty_average,
                 skeletons=skeletons,
                 skeletons_filtered=skeletons_average,
                 skeletons_msgs_rate=msgs_rate_skeletons,
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
            "msgs_rate_skeletons": msgs_rate_skeletons,
            "skeletons_pods_cpu": skeletons_pods_cpu,
            "skeletons_pods_gpu": skeletons_pods_gpu
        }
        logger.info('{}', str(info).replace("'", '"'))
        time.sleep(3)


if __name__ == '__main__':
    main()
