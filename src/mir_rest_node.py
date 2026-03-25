"""REST-based node for UR robots"""

from pathlib import Path
from typing import List, Optional

from mir_driver.mir_driver import MiR_Base
from typing_extensions import Annotated
from madsci.common.ownership import get_current_ownership_info
from madsci.common.types.node_types import RestNodeConfig
from madsci.node_module.helpers import action
from madsci.node_module.rest_node_module import RestNode
from madsci.common.types.location_types import LocationArgument

class MIRConfig(RestNodeConfig):
    """Configuration for the MIR REST node"""
    mir_host: str = "mirbase2.cels.anl.gov"
    map_name: str = "RPL"

class MIRNode:
    """A node to control the mobile MIR Base"""
  
    config: MIRConfig = MIRConfig()
    config_model = MIRConfig
    def startup_handler(self):
        """MIR startup handler."""
        
        self.mir = MiR_Base(mir_ip=self.config.mir_host, map_name=self.config.map_name)
        print("MIR Base online")

    def status_handler(self):
        """Periodically called to update the current status of the node."""
        """Returns the current state of the UR module"""
        if self.node_status.busy == False:
            robot_state = self.mir.get_state()
            if robot_state == "ERROR":
                self.node_status.errored = True
            elif robot_state == "EXECUTING":
                self.node_status.busy = True
                error = "Executing current mission, can still accept more missions."
            elif len(self.node_status.running_actions) == 0:
                self.node_status.busy = False

            

    @action
    def move(
        self,
        target_location: Annotated[LocationArgument, "Target location name"],
        description: Annotated[str, "Description of the location"],
        priority: Annotated[Optional[int], "Prority of the movement in the queue. Default is 0."],
    ) -> None:
        """Sends a move command to the MIR Base"""
        self.mir.move(
            location_name=target_location.representation,
        )
        




    @action
    def dock(self, 
        target_location: Annotated[LocationArgument, "Name of the docking location"],
    ) -> None:
        """Sends a docking command to the MIR Base"""
        self.mir.dock(
            location_name=target_location.representation,
        )
        self.mir.wait_until_finished()

    @action
    def queue_mission(
        self,
        name: Annotated[List[float], "Name of the mission"],
        mission: Annotated[List[dict], "A list of action dictionaries"],
        description: Annotated[str, "Description of the mission"],
        priority: Annotated[Optional[int], "Prority of the mission in the queue. Defult is 1"],
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
    def abort_mission_queue(
        self
    ) -> None:
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
    MIR_node.start_node
