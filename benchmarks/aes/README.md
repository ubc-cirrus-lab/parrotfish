# Deploying Function

### Creating New Lambda Function

1. In the AWS Lambda panel create a new function from scratch with these configurations:
    - **Function name:** pyaes
    - **Runtime:** Python 3.9
    - **Architecture:** x86_64

2. Copy the function code to the code source editor in Lambda's panel and deploy it.

3. Create a Function URL through the function's configuration menu.

### Adding Dependencies

This lambda function requires `pyaes` python package. To add pyaes package to the deployed function you need to add it
as a layer:

1. Create an empty folder to contain the dependencies:
   ```
   mkdir -p pyaes/python/lib/python3.9/site-packages
   ```
2. Install the dependency in the folder:
   ```
   pip3 install pyaes -t pyaes/python/lib/python3.9/site-packages/
   ```
3. Zip the `python` folder:
   ```
   zip -r pyaes.zip pyaes/*
   ```
4. In the AWS Lambda panel go to Layer section and create a new layer with these configurations:
   - **Name:** pyaes
   - Select **Upload a .zip file**
   - Upload the zip file created in the last step
   - **Compatible architectures:** select x86_64
   - **Compatible runtimes:** select Python 3.9
5. In the pyaes function panel under the Layers sections add a new layer.
   - Choose the custom layer that was created in the last step in the dropdown menu.

You should be able to use the function as intended with the function url now.