"""REST-based node for UR robots"""

import datetime
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


@rest_module.startup()
def mir_startup(state: State):
    """MIR startup handler."""
    state.mir = None
    state.mir = MiR_Base(mir_ip=state.mir_host, mir_key=state.mir_key)
    print("MIR Base online")


@rest_module.state_handler()
def state(state: State):
    """Returns the current state of the UR module"""
    if state.status not in [
        ModuleStatus.BUSY,
        ModuleStatus.ERROR,
        ModuleStatus.INIT,
        None,
    ] or (state.action_start and (datetime.datetime.now() - state.action_start > datetime.timedelta(0, 2))):
        # * Gets robt status
        # status = state.mir.status() #TODO: FIX status function to return a status
        # if status == "Error":
        #     state.status = ModuleStatus.ERROR
        # elif status == "BUSY":
        #     state.status = ModuleStatus.BUSY
        # else:
        state.status = ModuleStatus.IDLE
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
    priority: Annotated[Optional[int], "Prority of the movement in the queue. Default is 1"],
) -> StepResponse:
    """Sends a move command to the MIR Base"""
    state.move(
        location_name=target_location,
    )
    return StepResponse.step_succeeded(f"MIR Base moved to the location: {target_location} ")


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
    state.dock(
        location_name=target_location,
    )
    return StepResponse.step_succeeded(f"MIR Base moved to the location: {target_location} ")


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
    state.post_mission_to_queue(
        mission_name=name,
        act_param_dict=mission,
        description=description,
        priority=priority,
    )
    return StepResponse.step_succeeded(f"Mission {name} is sent to MIR Base")


@rest_module.action(
    name="abort_mission_queue",
    description="Send a abort_mission_queue command to the MIR Base",
)
def abort_mission_queue(
    state: State,
    action: ActionRequest,
) -> StepResponse:
    """Aborts all the missions in the queue"""
    state.abort_mission_queue()
    return StepResponse.step_succeeded("Missions aborted")


if __name__ == "__main__":
    rest_module.start()
