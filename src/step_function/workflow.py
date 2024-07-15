import json

import boto3

from states import State, Task, Parallel, Map, Workflow


def create_state(name, state_def: dict) -> State:
    """Create a State object from a state definition."""
    if state_def["Type"] == "Task":
        arn = state_def["Parameters"]["FunctionName"]
        return Task(name, arn)

    elif state_def["Type"] == "Parallel":
        parallel = Parallel(name)
        for branch_def in state_def["Branches"]:
            branch = create_workflow(branch_def)
            parallel.add_branch(branch)
        return parallel

    elif state_def["Type"] == "Map":
        map_state = Map(name)
        workflow = create_workflow(state_def["Iterator"])
        map_state.set_workflow(workflow)
        return map_state

    else:
        return State(name)  ## should throw an exception


def create_workflow(workflow_def: dict) -> Workflow:
    """Create a Workflow object from a workflow definition."""
    workflow = Workflow()

    state_name = workflow_def["StartAt"]  # starting state
    while 1:
        # add state to workflow
        state_def = workflow_def["States"][state_name]
        workflow.add_state(create_state(state_name, state_def))

        # go to next state
        if "Next" in state_def:
            state_name = state_def["Next"]
        elif "End" in state_def:
            break  # end of workflow
        else:
            break  ## should throw an exception

    return workflow


def get_step_func_def(arn: str) -> dict:
    """Get a step function's definition."""
    try:
        client = boto3.client("stepfunctions")
        response = client.describe_state_machine(stateMachineArn=arn)
        definition = json.loads(response["definition"])
        return definition
    except Exception as e:
        print(f"Error retrieving state machine: {e}")
        return []
