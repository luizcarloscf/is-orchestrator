# is-orchestrator

Service Orchestrator for the Intelligent Space

## Services

Under the scope of this project we have the following services:

* is-skeletons-detector
    * [luizcarloscf/is-skeletons-detector:0.0.3] (CPU version)
    * [luizcarloscf/is-skeletons-detector:0.0.3-openpose] (GPU version)
* is-skeletons-grouper
    * [luizcarloscf/is-skeletons-grouper:0.0.4]
* is-gesture-recognizer
    * [luizcarloscf/is-gesture-recognizer:0.0.7]

## About

The following service has two states:


| State | Services                 | Description|
|-------|--------------------------|------------|
|Low   |<ul><li>[luizcarloscf/is-skeletons-detector:0.0.3]</li></ul>  | The skeletons detector service stay running on CPU and expose the Number of Skeletons to Prometheus
|High    |<ul><li>[luizcarloscf/is-skeletons-detector:0.0.3-openpose]</li><li>[luizcarloscf/is-skeletons-grouper:0.0.4]</li><li>[luizcarloscf/is-gesture-recognizer:0.0.7]</li></ul> | When the number of skeletons is greater than a certain value, this state is triggered. Here we have the following metrics exposed on prometheus: Number of Skeletons and Uncertainty of a Gesture.


When this service is in the high state the fps is adjusted until an uncertainty is obtained within a certain tolerance.


It is important to remember that for this service work as expected, it depends on the following other services:

* [labviros/is-frame-transformation]
* [labviros/is-cameras] or [luizcarloscf/mock-cameras]


## References

* [labviros/is-skeletons-detector]
* [labviros/is-skeletons-grouper]

[luizcarloscf/is-skeletons-detector:0.0.3]: https://hub.docker.com/r/luizcarloscf/is-skeletons-detector 
[luizcarloscf/is-skeletons-detector:0.0.3-openpose]: https://hub.docker.com/r/luizcarloscf/is-skeletons-detector
[luizcarloscf/is-skeletons-grouper:0.0.4]: https://hub.docker.com/r/luizcarloscf/is-skeletons-grouper
[luizcarloscf/is-gesture-recognizer:0.0.7]: https://hub.docker.com/r/luizcarloscf/is-gesture-recognizer
[luizcarloscf/mock-cameras]: https://github.com/luizcarloscf/mock-cameras
[labviros/is-skeletons-detector]: https://github.com/labviros/is-skeletons-detector
[labviros/is-skeletons-grouper]: https://github.com/labviros/is-skeletons-grouper
[labviros/is-frame-transformation]: https://github.com/labviros/is-frame-transformation
[labviros/is-cameras]: https://github.com/labviros/is-cameras
