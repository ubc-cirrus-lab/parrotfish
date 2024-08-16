from src.objective.parametric_function import ParametricFunction
from src.step_function.step_function import Task, Map, Workflow


class StepFunctionOptimization():
    def __init__(self):
        workflow = self._create_workflow()
        tasks, time = workflow.get_critical_path()
        pass

    def _create_workflow(self) -> Workflow:
        workflow = Workflow()

        # Define the Task states
        task1 = Task(name='Get Input',
                     function_name='VideoAnalyticsGetInput:$LATEST')
        task1.param_function = ParametricFunction(params=[2., 0., 0.])
        task1.memory_size = 128

        task2 = Task(name='Video Streaming',
                     function_name='VideoAnalyticsStreaming:$LATEST')
        task2.param_function = ParametricFunction(params=[3436.25722795, 47451.13078245, 359.66527814])
        task2.memory_size = 1284

        task3 = Task(name='Decoder',
                     function_name='VideoAnalyticsDecoder:$LATEST')
        task3.param_function = ParametricFunction(params=[1.43282114e+09, -1.43282034e+09, -8.71342635e+09])
        task3.memory_size = 128

        # Define the Map state with 3 iterations
        map_state = Map(name="Map")

        # Define iterations with their respective param_functions
        iteration1 = Workflow()
        task1_iter1 = Task(name='Image Recognition',
                           function_name='VideoAnalyticsRecognition:$LATEST:1')
        task1_iter1.param_function = ParametricFunction(params=[500.77557129, 71060.38888613, 101.85462902])
        task1_iter1.memory_size = 1111
        iteration1.add_state(task1_iter1)

        iteration2 = Workflow()
        task1_iter2 = Task(name='Image Recognition',
                           function_name='VideoAnalyticsRecognition:$LATEST:2')
        task1_iter2.param_function = ParametricFunction(params=[246.80351563, 6286.15337624, 484.70156191])
        task1_iter2.memory_size = 1111
        iteration2.add_state(task1_iter2)

        iteration3 = Workflow()
        task1_iter3 = Task(name='Image Recognition',
                           function_name='VideoAnalyticsRecognition:$LATEST:3')
        task1_iter3.param_function = ParametricFunction(params=[318.85026003, 6551.93103995, 240.16171562])
        task1_iter3.memory_size = 1111
        iteration3.add_state(task1_iter3)

        map_state.add_iteration(iteration1)
        map_state.add_iteration(iteration2)
        map_state.add_iteration(iteration3)

        # Add states to the workflow
        workflow.add_state(task1)
        workflow.add_state(task2)
        workflow.add_state(task3)
        workflow.add_state(map_state)

        return workflow


if __name__ == "__main__":
    StepFunctionOptimization()
