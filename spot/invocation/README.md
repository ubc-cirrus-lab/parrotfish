# AWS Function Invocator
Automatic invocator is the tool to trigger benchmark functions to produce logs for model fitting and error calculation and waits for the data to be available on the cloud for further retrieval. It is based on the source code of an open-source tool, FaaSProfiler by Princeton University. 

Adapted form [FaaSProfiler](https://github.com/PrincetonUniversity/faas-profiler).
## Initiliaztion and Invocation
The invocator takes a user-defined workload JSON file on initialization and asynchronously invokes all the functions instances in it on `invoke_all()`. The memory size limit is 128MB by default and it can be optionally specified when calling `invoke_all()`.
```
ivk = AWSFuncctionInvocator(<path/to/workload>)
ivk.invoke_all(<memory_size>)
```

The software module takes a JSON file with serverless function metadata as input and sends multiple asynchronous requests to trigger the functions with Boto3 based on a configuration file. Serverless function invocations are observed to follow statistical distribution patterns. In order to emulate the aforementioned statistical distribution pattern with our function invocator, our module requires four parameters

### Workload File Structure
1. **Invocation Pattern:** This parameter controls the distribution of time intervals between invocations of a function. It implements uniform and Poisson distributions, which are the most common invocation patterns for serverless functions based on information from our client. In addition, a user can replay an invocation pattern from the actual usage of their serverless function. 
Whether a function is loaded in the CPU(warm start) can affect the runtime and cost greatly. Letting users specify the invocation distribution that most closely matches their function’s workload minimizes the error in profiling and provides more accurate data for optimization. 

2. **Invocation Rate:** The invocation rate specifies the average frequency of invocation within the specified distribution. This allows users to control the volume and intensity of invocation to accurately resemble the real-life invocation distribution.

3. **Function Input(Payload):** The input group to be used in a cycle of invocation sequence is stored in a separate JSON file and the path to this file is specified in the invocation configuration file. Having this separation enables quick modification of the input group, which can save development and deployment time. 

4. **Invocation Duration and Active Duration:** Users can define the duration of an invocation run (e.g. 15s) and the active window for a function within that run (e.g. 10~15s of the invocation duration). Such design gives users the freedom to stack patterns together by having multiple instances running in the same invocation duration but under different active windows. The two durations can be set to be the same if no such customization is desired.

### Log Propagation Waiter
There is a non-negligible delay between function invocation and the logs to be available for retrieval. To avoid inconsistency between function invocation and log retrieval, the invocator waits for the logs to propagate on AWS CloudWatch with a waiter module after each invocation run. The waiter takes a start time and the expected count of new logs then checks how many logs are available after the start time until the number is reached or timeout.

## Example Workload File
``` json
{
    "blocking_cli": false,
    "instances": {
        "instance1": {
            "activity_window": [
                5,
                10
            ],
            "application": "pyaes",
            "distribution": "Poisson",
            "host": "x8siu0es68.execute-api.us-east-2.amazonaws.com",
            "payload": "payload.json",
            "rate": 5,
            "resource": "/pyaes?format=json",
            "stage": "default"
        }
    },
    "random_seed": 100,
    "test_duration_in_seconds": 15,
    "test_name": "IntegrationTest1"
}
```