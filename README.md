# UBC SPOT
Created by Capstone Group 59

## Setup

### Requirements
- Python 3
- AWS CLI (configured with `aws configure`)
- MongoDB (by default, accessible on `localhost:27017`)

### Steps
1. Create and activate a virtualenv.
```bash
python3 -m venv spot-env
source spot-env/bin/activate
```

2. Install required packages.
```
pip install -r requirements.txt
```

3. Install SPOT as an editable package.
```bash
pip install -e .
```

4. Run it!
```bash
spot
```

