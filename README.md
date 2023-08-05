# Parametric Regression for Optimizing Serverless Functions (Parrotfish)

Save money on your serverless functions.  
Parrotfish is a configuration tool that helps developers rightsize their serverless functions by invoking them parallely a couple of times.

## Setup

### Requirements
- Python >= 3.8

#### Requirement to run parrotfish for AWS Lambda Function:
- AWS CLI (Configured with `aws configure`)

#### Requirement to run parrotfish for Google Cloud Function:
- gcloud CLI (Authenticate with your credentials: `gcloud auth application-default login`)
- Should enable the Cloud Billing API in your account.


### Steps
1. Create and activate a virtualenv.
```bash
python3 -m venv src-env
source src-env/bin/activate
```

2. Install the parrtofish package from the latest release. 
```bash
pip install ${path to parrotfish-version.whl}
```

3. Create the parrotfish configuration file.
Check the [configuration json object](src/configuration/README.md) to know configuration options.

4. Running it!
```bash
parrotfish ${path to the configuration file}
```
```text
optional arguments:
  -h, --help            show this help message and exit
  --path PATH, -p PATH  Path to the configuration file
  --verbose, -v         Set the logging level to INFO
  --apply               Apply optimized configuration
```
