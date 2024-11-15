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

2. Download and install the latest Parrotfish release.

```bash
pip install ${path to parrotfish-version.whl}
```

> **Note:** If you want to make changes to the code, you can install Parrotfish as an editable package:

```bash
export PACKAGE_VERSION="0.0.0"
pip install -e .
```

3. Create and optimize your Parrotfish configuration file. Check [here](src/configuration/README.md) to learn more about
   options and see some examples.

4. Run Parrotfish!

```bash
parrotfish --path ${path to the configuration file}
parrotfish --step-function --path ${path to the Step Function configuration file}
```

```text
Arguments:
  -h, --help            show this help message and exit
  --path PATH, -p PATH  Path to the configuration file
  --verbose, -v         Set the logging level to INFO
  --apply               Apply optimized configuration
  --step-function       Optimize for a Step Function
```

## Using custom models and objectives

To explore the effects of other objectives and models, you need to modify the `src/objective/objective.py` and
`src/objective/parametric_function.py` files.
If you need to change the sampling process, e.g. the initial samples, you need to modify the `src/sampling/sampler.py`
file.


## Extending support for additional Step Function state types

Currently, the `--step-function` mode is designed to optimize step functions that utilize `Task`, `Parallel`, and `Map` states. To extend support to additional state types, you'll need to modify two files:

1. `src/step_function/states.py`: Add new state types by creating classes that inherit from the base `State` class.

2. `src/step_function/step_function.py`: Update the `_create_state` function to parse the configuration files and create the state types.


## Support for 2D optimization for both CPU and memory configurations in GCP Cloud Functions V2

GCP Cloud Functions V2 allows decoupled configuration for CPU and memory allocations. Parrotfish can optimize the CPU and memory configuration of the V2 functions. To enable this feature, use `GCPv2` as the vendor in the config file.

## Related Papers, Articles, and Presentations

- [Parrotfish: Parametric Regression for Optimizing Serverless Functions](https://cirrus.ece.ubc.ca/papers/socc23_parrotfish.pdf) - Peer-reviewed research paper on Parrotfish presented at and published in the proceedings of the 2023 ACM Symposium on Cloud Computing (SoCC '23). [ACM Digital Library page](https://dl.acm.org/doi/10.1145/3620678.3624654).
- [Parrotfish-SF: Cost Optimization for AWS Step Functions](https://medium.com/@school.ziyiyang/parrotfish-sf-cost-optimization-of-aws-step-functions-9f73afd4e273) - An article written by Ziyi Yang on how he extended Parrotfish to support AWS Step Functions.
- [Parrotfish: An Advanced Multi-Objective Serverless Rightsizing Tool](https://www.serverlesscomputing.org/woscx3/presentations/6-ArshiaMoghimi-Parrotfish.pdf) - Arshia Moghimi's presentation on Parrotfish at the Third International Workshop on Serverless Computing Experience 2024 (WOSCx3).

## Acknowledgments

This work was supported by the Natural Sciences and Engineering Research Council of Canada (NSERC), Mitacs, and The
University of British Columbia (UBC).
This work was enabled by cloud resources made available to us by the Digital Research Alliance of Canada, Google Cloud,
Amazon Web Services, and Oracle Cloud Infrastructure.
