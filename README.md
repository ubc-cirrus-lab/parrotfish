# Parrotfish

<img src="./parrotfish_icon.jpeg" alt="parrotfish icon" width=20%>
<sup>Image made by Bing Image Creator powered by DALL·E 3. [Generated with AI ∙ October 10, 2023 at 5:09 p.m] </sup>
<br><br>
Parrotfish is a tool for optimizing configuration of serverless functions using parametric regression.
You can learn more about the architecture and performance of Parrotfish in our recent 2023 ACM Symposium on Cloud Computing (SoCC '23) paper: https://cirrus.ece.ubc.ca/papers/socc23_parrotfish.pdf

## Setup

### Requirements
- Python >= 3.8

#### Requirement to run Parrotfish for AWS Lambda Function:
- AWS CLI (Configured with `aws configure`)

#### Requirement to run Parrotfish for Google Cloud Function:
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

3. Create and optimize your Parrotfish configuration file. Check [here](src/configuration/README.md) to learn more.

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

## Acknowledgments

This work was supported by the Natural Sciences and Engineering Research Council of Canada (NSERC), Mitacs, and The University of British Columbia (UBC).
This work was enabled by cloud resources made available to us by the Digital Research Alliance of Canada, the Google Cloud Research Credits program, and the AWS Cloud Credit for Research program.
