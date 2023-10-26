# Parrotfish configuration file:

## Required Configurations Attributes:

```
{
    "function_name": The serverless function's name,
    "vendor": The cloud provider ("AWS" or "GCP"),
    "region": The serverless function's region,
    "payload": Payload to invoke the serverless function with (Required if "payloads" attribute is not provided),
    "payloads": [
        {
            "payload": Payload to invoke the serverless function with (Required),
            "weight": Impact of the exploration with this payload over the weighted average cost. (Required and Should be in [0, 1]),
        }...
    ] (Required if "payload" attribute is not provided. Sum of weights must be equal to 1),
}
```

## Optional Configuration Attributes:
```
{
    ...
    "memory_bounds": Array containing two memory values that represent the memory configuration bounds (Optional),
    "termination_threshold": When the knowledge value for the optimal memory configuration reaches this threshold the recommendation algorithm terminates. (Optional, Default is 3),
    "max_total_sample_count": The maximum size of the sample. (Optional, Default is 20),
    "min_sample_per_config": The minimum number of invocations per iteration. (Optional, Default is 4, minimum is 2),
    "dynamic_sampling_params": {
        "max_sample_per_config": The maximum number of samples we gather through dynamically (Default is 8),
        "coefficient_of_variation_threshold": When sample dynamically until we find a consistant enough. Consistency is measured by the coefficient of variation, 
                                              and when the calculated coefficient of variation reaches this threshold we terminate the dynamic sampling (Default is 0.05),
    } (Optional),
    "max_number_of_invocation_attempts": The maximum number of attempts per invocation when this number is reached an error is raised. (Optional, Default is 5)
    "constraint_execution_time_threshold": The execution time threshold constraint. We leverages the execution time model to recommend a configuration 
                                that minimizes cost while adhering to the specified execution time constraint. (Optional, Default is +infinity)
    "constraint_cost_tolerance_percent": The cost tolerance window (in percent). We leverage the cost model to recommend a configuration that maximizes performance while 
                             increasing the cost by at most X%, where X is the cost tolerance window . (Optional, Default is 0)
}
```


## Example single payload:
```json
{
    "function_name": "example_function",
    "vendor": "AWS",
    "region": "example_region",
    "payload": "payload"
}
```

## Example multiple payloads:
```json
{
    "function_name": "example_function",
    "vendor": "AWS",
    "region": "example_region",
    "payloads": [
      {
        "payload": "payload",
        "weight": 0.3
      },
      {
        "payload": "payload",
        "weight": 0.7
      }
    ]
}
```


### Replicating the results in the paper
To generate the results in the paper, we used these parameters:
```
termination_threshold=2
min_invocations=2
dynamic_sampling_params.max_sample_count=5
```
