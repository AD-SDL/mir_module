"""REST-based node for UR robots"""

from pathlib import Path
from typing import List, Optional

from fastapi.datastructures import State
from mir_driver.mir_driver import MiR_Base
from typing_extensions import Annotated
from wei.modules.rest_module import RESTModule
from wei.types.module_types import ModuleState, ModuleStatus
from wei.types.step_types import ActionRequest, StepResponse
from wei.utils import extract_version

rest_module = RESTModule(
    name="mir_node",
    version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
    description="A node to control the mobile MIR Base",
    model="Mir250",
)

rest_module.arg_parser.add_argument(
    "--mir_host",
    type=str,
    default="mirbase2.cels.anl.gov",
    help="Hostname or IP address to connect to MIR Base",
)
rest_module.arg_parser.add_argument(
    "--map_name",
    type=str,
    default="RPL",
    help="Hostname or IP address to connect to MIR Base",
)


@rest_module.startup()
def mir_startup(state: State):
    """MIR startup handler."""
    state.mir = None
    state.mir = MiR_Base(mir_ip=state.mir_host, map_name=state.map_name)
    print("MIR Base online")


@rest_module.state_handler()
def state(
    state: State,
):  # ** TBD, added "EXECUTING" state to "ModuleStatus" because MiR can be ready to accept missions but also executing them. Need to test if this works.
    """Returns the current state of the UR module"""
    if state.status not in [
        ModuleStatus.ERROR,
        ModuleStatus.INIT,
        None,
    ]:
        if state.mir.status == "BUSY":
            state.status = ModuleStatus.BUSY
        elif state.mir.status == "IDLE":
            state.status = ModuleStatus.IDLE
        else:
            state.mir.status = state.mir.get_state()
            if state.mir.status in ["READY", "IDLE"]:
                state.status = ModuleStatus.IDLE
            elif state.mir.status in ["PENDING", "EXECUTING"]:
                state.status = ModuleStatus.EXECUTING
            else:
                state.status = ModuleStatus.ERROR
    return ModuleState(status=state.status, error="")


@rest_module.action(
    name="move",
    description="Send a Move command to the MIR Base",
)
def move(
    state: State,
    action: ActionRequest,
    target_location: Annotated[List[dict], "Target location name"],
    description: Annotated[str, "Description of the location"],
    priority: Annotated[Optional[int], "Prority of the movement in the queue. Default is 0."],
) -> StepResponse:
    """Sends a move command to the MIR Base"""
    state.mir.move(
        location_name=target_location,
    )
    return StepResponse.step_succeeded()


@rest_module.action(
    name="wait_until_finished", description="Wait until previous mission is finished before proceeding."
)
def wait_until_finished(
    state: State,
    action: ActionRequest,
) -> StepResponse:
    """MIR Base continuously checks status of last sent mission before proceeding."""
    state.mir.wait_until_finished()
    return StepResponse.step_succeeded()


@rest_module.action(
    name="dock",
    description="Sends a dock command to the MIR Base",
)
def dock(
    state: State,
    action: ActionRequest,
    target_location: Annotated[List[dict], "Name of the docking location"],
) -> StepResponse:
    """Sends a docking command to the MIR Base"""
    state.mir.dock(
        location_name=target_location,
    )
    return StepResponse.step_succeeded()


@rest_module.action(
    name="queue_mission",
    description="Adds a new mission to the queue. A mission could have multiple movement actions",
)
def queue_mission(
    state: State,
    action: ActionRequest,
    name: Annotated[List[float], "Name of the mission"],
    mission: Annotated[List[dict], "A list of action dictionaries"],
    description: Annotated[str, "Description of the mission"],
    priority: Annotated[Optional[int], "Prority of the mission in the queue. Defult is 1"],
) -> StepResponse:
    """Sends a mission to the MIR Base which could have multiple movement actions"""
    state.mir.post_mission_to_queue(
        mission_name=name,
        act_param_dict=mission,
        description=description,
        priority=priority,
    )
    return StepResponse.step_succeeded()


@rest_module.action(
    name="abort_mission_queue",
    description="Send a abort_mission_queue command to the MIR Base",
)
def abort_mission_queue(
    state: State,
    action: ActionRequest,
) -> StepResponse:
    """Aborts all the missions in the queue"""
    state.mir.abort_mission_queue()
    return StepResponse.step_succeeded()


@rest_module.action(
    name="add_wait",
    description="Send a abort_mission_queue command to the MIR Base",
)
def add_wait(
    state: State,
    action: ActionRequest,
    delay_seconds: float,
) -> StepResponse:
    """Adds a wait mission to MIR Base"""
    state.mir.wait(delay_seconds)
    return StepResponse.step_succeeded()


if __name__ == "__main__":
    rest_module.start()
