import json
from typing import TextIO

import jsonschema

from src.configuration.defaults import *


class StepFunctionConfiguration:
    def __init__(self, config_file: TextIO):
        self._load_config_schema()

        # Setup default values
        self.dynamic_sampling_params = DYNAMIC_SAMPLING_PARAMS
        self.termination_threshold = TERMINATION_THRESHOLD
        self.max_total_sample_count = MAX_TOTAL_SAMPLE_COUNT
        self.min_sample_per_config = MIN_SAMPLE_PER_CONFIG
        self.max_number_of_invocation_attempts = MAX_NUMBER_OF_INVOCATION_ATTEMPTS

        # Parse the configuration file
        self._deserialize(config_file)

    def _load_config_schema(self):
        self._config_json_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Parrotfish for Step Function Configuration Schema",
            "description": "The configuration input's schema.",
            "type": "object",
            "properties": {
                "arn": {"type": "string"},
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
                "termination_threshold": {"type": "number", "minimum": 0},
                "max_total_sample_count": {"type": "integer", "minimum": 0},
                "min_sample_per_config": {"type": "integer", "minimum": 2},
                "dynamic_sampling_params": {
                    "type": "object",
                    "properties": {
                        "max_sample_per_config": {"type": "integer", "minimum": 0},
                        "coefficient_of_variation_threshold": {
                            "type": "number",
                            "minimum": 0,
                        },
                    },
                },
                "max_number_of_invocation_attempts": {"type": "integer", "minimum": 0},
            },
            "required": ["arn", "region", "payload"],
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
            j_dict["payload"] = json.dumps(j_dict["payload"])
            self.__dict__.update(**j_dict)