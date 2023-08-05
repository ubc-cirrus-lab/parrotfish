# Parrotfish configuration file:

## Basic Configuration:

```
{
    "function_name": The serverless function's name (Required),
    "vendor": The cloud provider "AWS" or "GCP" (Required),
    "region": The serverless function's region (Required),
    "payload": Payload to invoke the serverless function with (Required if payloads attribute not provided),
    "payloads": [
        {
            "payload": Payload to invoke the serverless function with (Required),
            "weight": Impact of the exploration with this payload over the weighted average cost. (Required and Should be in [0, 1]),
            "execution_time_threshold": The execution time threshold constraint. We leverages the execution time model to recommend a configuration 
                                        that minimizes cost while adhering to the specified execution time constraint. (Optional),
        }...
    ] (Constraint: sum of weights must be equal to 1!),
}
```

## Advanced configuration:
```
{
    ...
    
    "memory_bounds": Array containing two memory values that represent the memory configuration bounds (Optional),
    "termination_threshold": When the knowledge value for the optimal memory configuration reaches this threshold the recommendation algorithm terminates. (Optional),
    "max_sample_count": The maximum size of the sample. (Optional),
    "number_invocations": The minimum number of invocations per iteration. (Optional),
    "dynamic_sampling_params": {
        "max_sample_count": The maximum number of samples we gather through dynamically,
        "coefficient_of_variation_threshold": When sample dynamically until we find a consistant enough. Consistency is measured by the coefficient of variation, 
                                              and when the calculated coefficient of variation reaches this threshold we terminate the dynamic sampling,
    } (Optional),
    "max_number_of_invocation_attempts": The maximum number of attempts per invocation when this number is reached an error is raised. (Optional)
    "execution_time_threshold":  The execution time threshold constraint. We leverages the execution time model to recommend a configuration that minimizes cost while adhering to the specified
                                 execution time constraint. In case of multiple payloads this value will be applied to all the payloads if no execution_time_threshold attribute is present.
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
