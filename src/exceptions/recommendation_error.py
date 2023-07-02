class OptimizationError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)

    def __str__(self):
        return self.args[0]
