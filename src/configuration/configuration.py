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
        self.min_invocations = MIN_INVOCATIONS
        self.max_number_of_invocation_attempts = MAX_NUMBER_OF_INVOCATION_ATTEMPTS
        self.execution_time_threshold = None
        self.cost_tolerance_window = None
        self.memory_bounds = None

        # Parse the configuration file
        self._deserialize(config_file)

    def _load_config_schema(self):
        self._config_json_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Parrotfish Configuration Schema",
            "description": "The configuration input's schema.",
            "type": "object",
            "properties": {
                "function_name": {"type": "string"},
                "vendor": {"type": "string", "enum": ["AWS", "GCP"]},
                "region": {"type": "string"},
                "payload": {"anyOf": [{"type": "object"}, {"type": "array"}]},
                "payloads": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "payload": {
                                "anyOf": [{"type": "object"}, {"type": "array"}]
                            },
                            "weight": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["payload", "weight"],
                    },
                    "minItems": 1,
                },
                "memory_bounds": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "termination_threshold": {"type": "number", "minimum": 0},
                "max_sample_count": {"type": "integer", "minimum": 0},
                "min_invocations": {"type": "integer", "minimum": 0},
                "dynamic_sampling_params": {
                    "type": "object",
                    "properties": {
                        "max_sample_count": {"type": "integer", "minimum": 0},
                        "coefficient_of_variation_threshold": {
                            "type": "number",
                            "minimum": 0,
                        },
                    },
                },
                "max_number_of_invocation_attempts": {"type": "integer", "minimum": 0},
                "execution_time_threshold": {"type": "integer", "minimum": 1},
                "cost_tolerance_window": {"type": "integer", "minimum": 1},
            },
            "required": ["function_name", "vendor", "region"],
            "if": {"not": {"required": ["payload"]}},
            "then": {"required": ["payloads"]},
            "else": {"required": ["payload"]},
            "additionalProperties": False,
        }

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
