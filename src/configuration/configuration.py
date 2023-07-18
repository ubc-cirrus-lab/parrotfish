import json
import logging
import os
import sys
from typing import TextIO

import jsonschema

from .defaults import *


class Configuration:
    def __init__(self, config_file: TextIO = None):
        config_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config_file_schema.json"
        )
        with open(config_file_path) as config_file_schema:
            self._config_json_schema = json.load(config_file_schema)
        self._logger = logging.getLogger(__name__)

        # Setup default values
        self.dynamic_sampling_termination_threshold = TERMINATION_CV
        self.termination_threshold = TERMINATION_THRESHOLD
        self.sample_size = TOTAL_SAMPLE_COUNT
        self.number_invocations = DYNAMIC_SAMPLING_INITIAL_STEP
        self.max_dynamic_sample_size = DYNAMIC_SAMPLING_MAX
        self.max_number_of_invocation_attempts = MAX_NUMBER_INVOCATION_ATTEMPTS
        self.execution_time_threshold = None
        self.memory_bounds = None

        if config_file:
            self._deserialize(config_file)
            self.payload = json.dumps(self.payload)

    def _deserialize(self, f):
        try:
            j_dict = json.load(f)
            self._validate_config_schema(j_dict)
        except json.decoder.JSONDecodeError as e:
            self._logger.debug(e.args[0])
            print("Failed to deserialize the given file", file=sys.stderr)
            raise IOError
        except ValueError as e:
            self._logger.debug(e.args[0])
            print("Config schema not valid", file=sys.stderr)
            raise IOError
        else:
            self.__dict__.update(**j_dict)

    def _validate_config_schema(self, json_data):
        try:
            jsonschema.validate(instance=json_data, schema=self._config_json_schema)
        except jsonschema.exceptions.ValidationError as err:
            raise ValueError(err.args[0])
        return True
