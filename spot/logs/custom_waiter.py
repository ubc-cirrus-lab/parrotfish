# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Custom waiter for boto3 services from https://docs.aws.amazon.com/code-samples/latest/catalog/python-demo_tools-custom_waiter.py.html

from enum import Enum
import logging
import botocore.waiter
import jmespath

logger = logging.getLogger(__name__)


class WaitState(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class CustomWaiter:
    def __init__(
        self,
        name,
        operation,
        argument,
        acceptors,
        client,
        delay=10,
        max_tries=60,
        matcher="path",
    ):
        self.name = name
        self.operation = operation
        self.argument = argument
        self.client = client
        self.waiter_model = botocore.waiter.WaiterModel(
            {
                "version": 2,
                "waiters": {
                    name: {
                        "delay": delay,
                        "operation": operation,
                        "maxAttempts": max_tries,
                        "acceptors": [
                            {
                                "state": state.value,
                                "matcher": matcher,
                                "argument": argument,
                                "expected": expected,
                            }
                            for expected, state in acceptors.items()
                        ],
                    }
                },
            }
        )

        self.waiter = botocore.waiter.create_waiter_with_client(
            self.name, self.waiter_model, self.client
        )

    def __call__(self, parsed, **kwargs):
        """
        Handles the after-call event by logging information about the operation and its
        result.

        :param parsed: The parsed response from polling the operation.
        :param kwargs: Not used, but expected by the caller.
        """
        status = parsed
        for key in self.argument.split("."):
            if key.endswith("[]"):
                status = status.get(key[:-2])[0]
            else:
                status = status.get(key)
        logger.info("Waiter %s called %s, got %s.", self.name, self.operation, status)
        # print(f"Waiter {self.name} called {self.operation}, got {status}.")

    def _wait(self, **kwargs):
        """
        Registers for the after-call event and starts the botocore wait loop.

        :param kwargs: Keyword arguments that are passed to the operation being polled.
        """
        event_name = f"after-call.{self.client.meta.service_model.service_name}"
        self.client.meta.events.register(event_name, self)
        self.waiter.wait(**kwargs)
        self.client.meta.events.unregister(event_name, self)
