from spot.logs.custom_waiter import CustomWaiter, WaitState


class LogQueryWaiter(CustomWaiter):
    """Wait for a log query to finish"""

    def __init__(self, client, delay=10, max_tries=60, matcher="path"):
        acceptors = {"Complete": WaitState.SUCCESS, "Failed": WaitState.FAILURE}
        super().__init__(
            "LogQueryComplete",
            "GetQueryResults",
            "status",
            acceptors,
            client,
            delay,
            max_tries,
            matcher,
        )

    def wait(self, query_id: str) -> None:
        self._wait(queryId=query_id)
