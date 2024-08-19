from typing import Tuple

from src.exception.step_function_error import StepFunctionError
from src.logger import logger
from src.objective.parametric_function import ParametricFunction
from src.step_function.step_function import Task, Map, Workflow


class StepFunctionOptimization():
    def __init__(self):
        pass

    def optimize_step_function(self, workflow: Workflow, function_tasks_dict: dict, memory_increment: int,
                               constraint_execution_time_threshold: int):
        critical_path_tasks, critical_path_time = workflow.get_critical_path()
        logger.info(
            f"Start optimizing step function for execution time, time: {critical_path_time}ms, threshold: {constraint_execution_time_threshold}ms, cost: {workflow.get_cost()}.\n")

        # Initialize cost increase dict
        cost_increases = {}
        for function in function_tasks_dict:
            cost_increases[function] = 0.0
            for task in function_tasks_dict[function]:
                original_cost = task.get_cost(task.memory_size)
                new_cost = task.get_cost(task.memory_size + memory_increment)
                cost_increases[function] += new_cost - original_cost

        # Update memory sizes until execution time threshold is reached
        while critical_path_time > constraint_execution_time_threshold:
            time_reductions = {}

            # Iterate over tasks on critical path and calculate time reductions for each function
            for task in critical_path_tasks:
                if task.memory_size + memory_increment > 3008:
                    continue

                original_time = task.get_execution_time()
                new_time = task.get_execution_time(task.memory_size + memory_increment)

                if task.function_name not in time_reductions:
                    time_reductions[task.function_name] = 0.0
                time_reductions[task.function_name] += original_time - new_time

            # Find the function with the lowest cost to time reduction ratio
            best_function = None
            lowest_ratio = float('inf')
            for function_name in time_reductions:
                if time_reductions[function_name] > 0:
                    ratio = cost_increases[function_name] / time_reductions[function_name]
                    logger.debug(
                        f"ratio: {ratio}, {function_name}, {function_tasks_dict[function_name][0].memory_size}MB, {cost_increases[function_name]}, {time_reductions[function_name]}")

                    if ratio < lowest_ratio:
                        lowest_ratio = ratio
                        best_function = function_name

            # Increase memory size of best function, update cost increases
            if best_function:
                cost_increases[best_function] = 0.0
                for task in function_tasks_dict[best_function]:
                    task.increase_memory_size(memory_increment)
                    original_cost = task.get_cost()
                    new_cost = task.get_cost(task.memory_size + memory_increment)
                    cost_increases[best_function] += new_cost - original_cost
            else:
                raise StepFunctionError("Execution time threshold too low.")

            # Update critical path and time
            critical_path_tasks, critical_path_time = workflow.get_critical_path()
            logger.debug(
                f"Optimized function {best_function}, {task.memory_size}MB, time: {critical_path_time}ms, cost: {workflow.get_cost()}.\n")

        logger.info(
            f"Finish optimizing step function for execution time, time: {critical_path_time}ms, threshold: {constraint_execution_time_threshold}ms, cost: {workflow.get_cost()}.\n")

    def optimize_individual_function(self, workflow: Workflow, function_tasks_dict: dict, memory_increment: int,
                                     constraint_execution_time_threshold: int):
        _, critical_path_time = workflow.get_critical_path()

        if critical_path_time > constraint_execution_time_threshold:
            logger.info(
                f"Start optimizing individual tasks for execution time. time: {critical_path_time}, threshold: {constraint_execution_time_threshold}, cost: {workflow.get_cost()}.\n")
            percent = critical_path_time / constraint_execution_time_threshold
            for function in function_tasks_dict:
                for task in function_tasks_dict[function]:
                    original_time = task.get_execution_time()
                    logger.debug(f"{task.function_name}, original time: {original_time}")

                    while (task.get_execution_time() > original_time / percent
                           and task.memory_size + memory_increment <= 3008):
                        #     logger.debug(f"{task.function_name} exceeds maximum memory size.")
                        #     raise StepFunctionError("Execution time threshold too low.")
                        # else:
                        task.increase_memory_size(memory_increment)

                    logger.debug(
                        f"{task.function_name}, final time: {task.get_execution_time()}, target: {original_time / percent}, cost: {task.get_cost()}")
        else:
            logger.warning("Execution time is already below threshold.")

        _, critical_path_time = workflow.get_critical_path()
        logger.info(
            f"Finish optimizing individual tasks for execution time. time: {critical_path_time}ms, threshold: {constraint_execution_time_threshold}ms, cost: {workflow.get_cost()}.\n")

    def _create_workflow(self) -> Tuple[Workflow, dict]:
        workflow = Workflow()
        task_dict = {}

        def add_task_to_dict(task):
            if task.function_name not in task_dict:
                task_dict[task.function_name] = [task]
            else:
                task_dict[task.function_name].append(task)

        # Define the Task states
        task1 = Task(name='Get Input',
                     function_name='VideoAnalyticsGetInput:$LATEST')
        task1.param_function = ParametricFunction(params=[2., 0., 0.])
        task1.memory_size = 128
        add_task_to_dict(task1)

        task2 = Task(name='Video Streaming',
                     function_name='VideoAnalyticsStreaming:$LATEST')
        task2.param_function = ParametricFunction(params=[3436.25722795, 47451.13078245, 359.66527814])
        task2.memory_size = 1284
        add_task_to_dict(task2)

        task3 = Task(name='Decoder',
                     function_name='VideoAnalyticsDecoder:$LATEST')
        task3.param_function = ParametricFunction(params=[1.43282114e+09, -1.43282034e+09, -8.71342635e+09])
        task3.memory_size = 128
        add_task_to_dict(task3)

        # Define the Map state with 3 iterations
        map_state = Map(name="Map")

        # Define iterations with their respective param_functions
        iteration1 = Workflow()
        task1_iter1 = Task(name='Image Recognition 1',
                           function_name='VideoAnalyticsRecognition:$LATEST')
        task1_iter1.param_function = ParametricFunction(params=[500.77557129, 71060.38888613, 101.85462902])
        task1_iter1.memory_size = 1111
        iteration1.add_state(task1_iter1)
        add_task_to_dict(task1_iter1)

        iteration2 = Workflow()
        task1_iter2 = Task(name='Image Recognition 2',
                           function_name='VideoAnalyticsRecognition:$LATEST')
        task1_iter2.param_function = ParametricFunction(params=[246.80351563, 6286.15337624, 484.70156191])
        task1_iter2.memory_size = 1111
        iteration2.add_state(task1_iter2)
        add_task_to_dict(task1_iter2)

        iteration3 = Workflow()
        task1_iter3 = Task(name='Image Recognition 3',
                           function_name='VideoAnalyticsRecognition:$LATEST')
        task1_iter3.param_function = ParametricFunction(params=[318.85026003, 6551.93103995, 240.16171562])
        task1_iter3.memory_size = 1111
        iteration3.add_state(task1_iter3)
        add_task_to_dict(task1_iter3)

        map_state.add_iteration(iteration1)
        map_state.add_iteration(iteration2)
        map_state.add_iteration(iteration3)

        # Add states to the workflow
        workflow.add_state(task1)
        workflow.add_state(task2)
        workflow.add_state(task3)
        workflow.add_state(map_state)

        return workflow, task_dict


if __name__ == "__main__":
    stepFunctionOptimization = StepFunctionOptimization()
    workflow, function_tasks_dict = stepFunctionOptimization._create_workflow()
    stepFunctionOptimization.optimize_step_function(workflow, function_tasks_dict,
                                                    memory_increment=10, constraint_execution_time_threshold=6000)

    stepFunctionOptimization = StepFunctionOptimization()
    workflow, function_tasks_dict = stepFunctionOptimization._create_workflow()
    stepFunctionOptimization.optimize_individual_function(workflow, function_tasks_dict, memory_increment=10,
                                                          constraint_execution_time_threshold=6000)
