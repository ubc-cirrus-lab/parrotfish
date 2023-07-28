import json
import os
from typing import TextIO

import jsonschema

from .defaults import *


class Configuration:
    def __init__(self, config_file: TextIO):
        self._load_config_schema()

        # Setup default values
        self.dynamic_sampling_params = DYNAMIC_SAMPLING_PARAMS
        self.termination_threshold = TERMINATION_THRESHOLD
        self.max_sample_count = MAX_SAMPLE_COUNT
        self.number_invocations = NUMBER_INVOCATIONS
        self.max_number_of_invocation_attempts = MAX_NUMBER_OF_INVOCATION_ATTEMPTS
        self.execution_time_threshold = None
        self.memory_bounds = None

        # Parse the configuration file
        self._deserialize(config_file)

    def _load_config_schema(self):
        config_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config_file_schema.json"
        )
        with open(config_file_path) as config_file_schema:
            self._config_json_schema = json.load(config_file_schema)

    def _deserialize(self, config_file: TextIO):
        try:
            j_dict = json.load(config_file)
            jsonschema.validate(instance=j_dict, schema=self._config_json_schema)

        except json.decoder.JSONDecodeError as e:
            raise ValueError(
                f"Please make sure to provide a valid json object in file {config_file.name}: \n{e.args[0]}"
            )

        except jsonschema.exceptions.ValidationError as e:
            raise ValueError(
                f"Please make sure to provide a valid json object in file {config_file.name}: \n{e.args[0]}"
            )

        else:
            if "payloads" in j_dict:
                for entry in j_dict["payloads"]:
                    entry["payload"] = json.dumps(entry["payload"])
                    entry["execution_time_threshold"] = j_dict["execution_time_threshold"] if "execution_time_threshold" in j_dict else None
                # Validate that sum of weights is 1.
                if sum([entry["weight"] for entry in j_dict["payloads"]]) != 1:
                    raise ValueError(
                        f"Please make sure that the weights in {config_file.name} are in [0,1] interval "
                        f"and that their sum is 1"
                    )

            if "payload" in j_dict:
                payload_str = json.dumps(j_dict["payload"])
                j_dict["payloads"] = [{"payload": payload_str, "weight": 1}]
                del j_dict["payload"]

            self.__dict__.update(**j_dict)
