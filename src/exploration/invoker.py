from abc import ABC, abstractmethod


class Invoker(ABC):
    """This class provides the operation of serverless function's invocation."""

    def __init__(self, function_name: str):
        self.function_name = function_name

    @abstractmethod
    def invoke(self, payload: str) -> str:
        """Invokes the serverless function with the payload @payload and returns the response.

        Args:
            payload (str): Payload to invoke the function with.

        Returns:
            str: The logs returned by the function in response to the invocation.

        Raises:
            InvocationError: If the invocation cannot be performed. (Possibly function not found, user not authorised,
            or payload is wrong ...), or if the maximum number of exploration's attempts is reached.
        """
        pass
