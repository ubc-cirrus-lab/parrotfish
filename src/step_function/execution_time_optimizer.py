from src.exception.step_function_error import StepFunctionError
from src.logger import logger


class ExecutionTimeOptimizer:
    def __init__(self, workflow, function_tasks_dict, config):
        self.workflow = workflow
        self.function_tasks_dict = function_tasks_dict
        self.memory_increment = config.memory_size_increment
        self.execution_time_threshold = config.constraint_execution_time_threshold

    def optimize_for_execution_time_constraint(self):
        """Optimize the step function for execution time constraints."""
        if self.execution_time_threshold is None:
            logger.warning("No execution time threshold.")
            return

        critical_path_tasks, critical_path_time = self.workflow.get_critical_path()
        logger.info(
            f"Start optimizing step function for execution time, time: {critical_path_time}ms, threshold: {self.execution_time_threshold}ms, cost: {self.workflow.get_cost()}."
        )

        cost_increases = self._initialize_cost_increases()

        while critical_path_time > self.execution_time_threshold:
            time_reductions = self._calculate_time_reductions(critical_path_tasks)
            best_function = self._find_best_function_to_optimize(cost_increases, time_reductions)

            if best_function:
                self._update_memory_size_and_cost(best_function, cost_increases)
            else:
                raise StepFunctionError("Execution time threshold too low.")

            critical_path_tasks, critical_path_time = self.workflow.get_critical_path()
            logger.debug(
                f"Optimized function {best_function}, time: {critical_path_time}ms, cost: {self.workflow.get_cost()}.\n"
            )

        logger.info(
            f"Finish optimizing step function for execution time, time: {critical_path_time}ms, threshold: {self.execution_time_threshold}ms, cost: {self.workflow.get_cost()}.\n"
        )
        self._print_memory_sizes()

    def _initialize_cost_increases(self):
        """Initialize the cost increases for each function."""
        cost_increases = {}
        for function in self.function_tasks_dict:
            cost_increases[function] = 0.0
            for task in self.function_tasks_dict[function]:
                original_cost = task.get_cost(task.memory_size)
                new_cost = task.get_cost(task.memory_size + self.memory_increment)
                cost_increases[function] += new_cost - original_cost
        return cost_increases

    def _calculate_time_reductions(self, critical_path_tasks):
        """Calculate time reductions for tasks on the critical path."""
        time_reductions = {}
        for task in critical_path_tasks:
            if task.memory_size + self.memory_increment > task.max_memory_size:
                continue

            original_time = task.get_execution_time()
            new_time = task.get_execution_time(task.memory_size + self.memory_increment)

            if task.function_name not in time_reductions:
                time_reductions[task.function_name] = 0.0
            time_reductions[task.function_name] += original_time - new_time
        return time_reductions

    def _find_best_function_to_optimize(self, cost_increases, time_reductions):
        """Find the function with the lowest cost to time reduction ratio."""
        best_function = None
        lowest_ratio = float('inf')
        for function_name in time_reductions:
            if time_reductions[function_name] > 0:
                ratio = cost_increases[function_name] / time_reductions[function_name]
                logger.debug(
                    f"ratio: {ratio}, {function_name}, {self.function_tasks_dict[function_name][0].memory_size}MB, {cost_increases[function_name]}, {time_reductions[function_name]}"
                )

                if ratio < lowest_ratio:
                    lowest_ratio = ratio
                    best_function = function_name
        return best_function

    def _update_memory_size_and_cost(self, best_function, cost_increases):
        """Increase memory size of the best function and update cost increases."""
        cost_increases[best_function] = 0.0
        for task in self.function_tasks_dict[best_function]:
            task.increase_memory_size(self.memory_increment)
            original_cost = task.get_cost()
            new_cost = task.get_cost(task.memory_size + self.memory_increment)
            cost_increases[best_function] += new_cost - original_cost

    def _print_memory_sizes(self):
        """Print memory sizes after optimization."""
        print("Finish optimizing step function for execution time, optimized memory sizes:")
        for function in self.function_tasks_dict:
            print(f"{function}: {self.function_tasks_dict[function][0].memory_size}MB")
