### In order to add a new benchmark
1. Create a new directory in this current directory
2. cd to this directory: create config.json, workload.json(empty) and payload.json
3. Create main.py, create execute<benchmark_name> function, inside this function instantiate Spot instance and call execute on it
4. call execute<benchmark_name> in main.py under spot directory