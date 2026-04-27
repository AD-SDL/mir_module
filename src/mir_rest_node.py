"""REST-based node for UR robots"""

from typing import List, Optional

from madsci.common.types.location_types import LocationArgument
from madsci.common.types.node_types import RestNodeConfig
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from typing_extensions import Annotated

from mir_interface.mir_interface import MIRBase


class MIRConfig(RestNodeConfig):
    """Configuration for the MIR REST node"""

    mir_host: str = "mirbase2.cels.anl.gov"
    map_name: str = "RPL"


class MIRNode(RestNode):
    """A node to control the mobile MIR Base"""

    config: MIRConfig = MIRConfig()
    config_model = MIRConfig

    def startup_handler(self) -> None:
        """MIR startup handler."""

        self.mir = MIRBase(mir_ip=self.config.mir_host, map_name=self.config.map_name)
        self.mir.create_position_dict()

    def status_handler(self) -> None:
        """Periodically called to update the current status of the node."""
        if not self.node_status.busy:
            robot_state = self.mir.get_state()
            if robot_state == "ERROR":
                self.node_status.errored = True

    def state_handler(self) -> str:
        """Returns the current state of the MIR Base"""
        return self.mir.get_state()

    @action
    def move(
        self, target_location: Annotated[LocationArgument, "Target location name"]
    ) -> None:
        """Sends a move command to the MIR Base"""
        self.mir.move(
            location_name=target_location.representation["location_name"],
        )

    @action
    def dock(
        self,
        target_location: Annotated[LocationArgument, "Name of the docking location"],
    ) -> None:
        """Sends a docking command to the MIR Base"""
        self.mir.dock(
            location_name=target_location.representation["location_name"],
        )
        self.mir.wait_until_finished()

    @action
    def queue_mission(
        self,
        name: Annotated[List[float], "Name of the mission"],
        mission: Annotated[List[dict], "A list of action dictionaries"],
        description: Annotated[str, "Description of the mission"],
        priority: Annotated[
            Optional[int], "Prority of the mission in the queue. Defult is 1"
        ],
    ) -> None:
        """Sends a mission to the MIR Base which could have multiple movement actions"""
        self.mir.post_mission_to_queue(
            mission_name=name,
            act_param_dict=mission,
            description=description,
            priority=priority,
        )
        self.mir.wait_until_finished()

    @action
    def abort_mission_queue(self) -> None:
        """Aborts all the missions in the queue"""
        self.mir.abort_mission_queue()

    @action
    def add_wait(
        self,
        delay_seconds: float,
    ) -> None:
        """Adds a wait mission to MIR Base"""
        self.mir.wait(delay_seconds)


if __name__ == "__main__":
    MIR_node = MIRNode()
    MIR_node.start_node()
