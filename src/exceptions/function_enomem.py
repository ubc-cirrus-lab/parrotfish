class FunctionENOMEM(Exception):
    def __init__(self):
        super().__init__("The memory configured is not enough for the function's execution.")

    def __str__(self):
        return self.args[0]
