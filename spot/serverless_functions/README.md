### In order to add a new benchmark
1. Create a new directory in this current directory
2. cd to this directory: create config.json, workload.json(empty) and payload.json
    - If the folder name in `/benchmarks` is different from the function's name on lambda, `folder_name` needs to be specified in config.json
    - payload.json needs to be an array of function inputs and the invocator will iterate through this list
    - more detials on how to structure the files [here](/spot/invocation)
3. Create main.py, create execute<benchmark_name> function, inside this function instantiate Spot instance and call execute on it
4. call execute<benchmark_name> in main.py under spot directory
