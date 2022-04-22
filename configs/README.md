### In order to add a new configuration (for a lambda function)
1. Create a new directory in this current directory
2. cd to this directory: create config.json and payload.json
    - payload.json needs to be an array of function inputs and the invocator will iterate through this list
    - Observe other configurations in this directory to see how to properly structure the config.json and payload.json file. The workload.json file will be generated automatically after invocating the lambda function
    - More details on how invocation works [here](/spot/invocation)
3. Invoke the function based on the directory name. E.g. "spot func -i" will invoke a function configured under the directory "func"
