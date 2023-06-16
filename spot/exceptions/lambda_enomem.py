class LambdaENOMEM(Exception):
    def __init__(self):
        super().__init__("The memory configured is not enough for the function execution.")
