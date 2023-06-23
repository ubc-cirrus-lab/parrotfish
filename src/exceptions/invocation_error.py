class InvocationError(Exception):
    def __init__(self, msg):
        super().__init__(msg)

    def __str__(self):
        return self.args[0]
