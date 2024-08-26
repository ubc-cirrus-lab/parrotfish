from src.step_function.states import Parallel, Map, Workflow


class TestStates:
    def test_parallel_state_add_branch(self):
        # Arrange
        parallel_state = Parallel(name="test_parallel")
        workflow1 = Workflow()
        workflow2 = Workflow()
        # Act
        parallel_state.add_branch(workflow1)
        parallel_state.add_branch(workflow2)
        # Assert
        assert len(parallel_state.branches) == 2
        assert parallel_state.branches[0] == workflow1
        assert parallel_state.branches[1] == workflow2

    def test_map_state_set_workflow(self):
        # Arrange
        map_state = Map(name="test_map")
        workflow = Workflow()
        # Act
        map_state.add_iteration(workflow)
        # Assert
        assert len(map_state.iterations) == 1
        assert map_state.iterations[0] == workflow
