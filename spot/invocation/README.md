# AWS Function Invocator
## Initiliaztion and Invocation
The invocator takes a user-defined workload JSON file on initialization and asynchronously invokes all the functions instances in it on `invoke_all()`. The memory size limit is 128MB by default and it can be optionally specified when calling `invoke_all()`.
```
ivk = AWSFuncctionInvocator(<path/to/workload>)
ivk.invoke_all(<memory_size>)
```
The invocator uses IAM Key to authenticate. Make sure you have valid environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` set.
## Workload Structure
Below is an example of workload input to the invocator
``` json
{                                                          
    "test_name": "test",
    "test_duration_in_seconds": 15,
    "random_seed": 100,
    "blocking_cli": false,
    "instances":{
        "instance1":{
            "application": "chameleon",
            "distribution": "Poisson",
            "rate": 5,
            "activity_window": [5, 10],
            "payload": "poisson.json",
            "host": "ng11cbhnw7.execute-api.us-west-1.zonaws.com",
            "stage":"default",
            "resource":"chameleon"
        },
        "instance2":{
            "application": "chameleon",
            "interarrivals_list": [5,0.13,0.15,0.8,0.1,0.13,0.13,0.1,0.4],
            "host": "ng11cbhnw7.execute-api.us-west-1.zonaws.com",
            "stage":"default",
            "resource":"chameleon"
        },
    }
}
```

`host`, `stage` and `resources` are the three key components to make the HTTP call. All three are from the API endpoint of a function, which has the format of `https://<host>/<stage>/<resource>`. For instance1 in the example, the API endpoint is `https://ng11cbhnw7.execute-api.us-west-1.amazonaws.com/default/chameleon` 

To use a customized invocation interval, define `interarrival_list` instead of `distribution` as in `instance2`. `interarrival_list` has a higher priority than distribution so if both are specified the customized interarrival time will be used for invocation.

`payload` is the path to a JSON file with cloud function inputs. Can skip if the function does not require any input.

