#!/usr/bin/env python3
"""
Driver code for the MiR 250 Robotic base.
"""

import datetime as dt
import json
import time
from typing import Optional

import requests


class MIRBase:
    """Main Driver Class for the MiR Robotic base."""

    def __init__(
        self,
        mir_ip: str = "mirbase2.cels.anl.gov",
        mir_key: str = "Basic RGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA==",
        map_name: Optional[str] = None,
        filename: str = "locations.json",
    ) -> None:
        """
        Initialize the MiRBase class with default or provided values.
        """
        self.mir_ip = mir_ip
        self.mir_key = mir_key
        self.host = f"http://{self.mir_ip}/api/v2.0.0/"

        # Set up the request headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": self.mir_key,
        }

        self.filename = filename
        self.map_name = map_name
        self.current_map = self.get_map()
        self.map_guid = self.current_map["guid"]
        self.group_id = self.get_user_group_id()
        self.action_dict = self.create_action_dict()
        self.position_dict = self.create_position_dict()
        self.curr_mission_queue_id = self.set_mission_queue_id()
        self.status = self.get_state()
        self.locations_dict = {}

    def get_map(self) -> dict:
        """
        Retrieve the current map for the MiR base.

        If the map name is not set, the first map from the list will be used.
        Otherwise, it tries to match the map name with the available maps.
        If no match is found, it defaults to the first map.

        Returns:
            dict: The map data of the current map.
        """
        maps = self.receive_response("maps")

        if not self.map_name:
            current_map = maps[0]
        else:
            current_map = list(filter(lambda map: map["name"] == self.map_name, maps))
            if not current_map:
                current_map = maps[0]

        return current_map[0]

    def get_actions(self, printq: bool = False) -> list:
        """
        Retrieve all valid action types and their descriptions.

        Args:
            printq (bool): If True, print the retrieved actions. Defaults to False.

        Returns:
            list: A list of actions available on the MiR base.
        """

        return self.receive_response("actions", printq)

    def get_action_type(self, action_type: str, printq: bool = False) -> dict:
        """
        Retrieve and print action parameters for a given action type.

        Args:
            action_type (str): The type of action to retrieve.
            printq (bool): If True, print the action parameters. Defaults to False.

        Returns:
            dict: The parameters for the specified action type.
        """

        url = f"actions/{action_type}"
        return self.receive_response(url, printq)

    def list_missions(self, printq: bool = False) -> dict:
        """
        List all created missions for the MiR base.

        Args:
            printq (bool): If True, print the list of missions. Defaults to False.

        Returns:
            list: A list of all missions created for the MiR base.
        """

        return self.receive_response("missions", printq)

    def get_mission_queue(self, printq: bool = False) -> dict:
        """
        Retrieve all missions in the queue since the last mission queue ID.

        Args:
            printq (bool): If True, print the list of missions in the queue. Defaults to False.

        Returns:
            list: A list of missions posted to the queue since the last session.
                Returns None if no missions were found.
        """
        search = {
            "filters": [
                {
                    "fieldname": "id",
                    "operator": ">",
                    "value": self.curr_mission_queue_id,
                }
            ]
        }
        return self.receive_response("mission_queue", printq, None, search)

    def abort_mission_queue(self) -> dict:
        """
        Abort all pending and executing missions in the mission queue.

        Returns:
            dict: The response from the MiR base after aborting the missions.
        """

        return self.delete("mission_queue", False, "All missions aborted.")

    def clear_mission_queue(self) -> str:
        """
        Clear the current mission queue by setting a new mission queue ID.

        Returns:
            str: The new mission queue ID.
        """
        self.curr_mission_queue_id = self.set_mission_queue_id()
        return self.curr_mission_queue_id

    def find_mission_in_queue(self, mission_name: str) -> None:
        """
        Find and print mission and action details for the given mission name in the queue.

        Args:
            mission_name (str): The name of the mission to search for.

        Returns:
            None
        """
        search = {
            "filters": [{"fieldname": "name", "operator": "=", "value": mission_name}]
        }
        mission = self.receive_response("missions", False, None, search)

        if not mission:
            return

        mission_guid = mission[0].get("guid")
        search = {
            "filters": [
                {"fieldname": "mission_id", "operator": "=", "value": mission_guid},
                {
                    "fieldname": "id",
                    "operator": ">",
                    "value": self.curr_mission_queue_id,
                },
            ]
        }

        mission_queue = self.receive_response("mission_queue", False, None, search)

        if not mission_queue:
            return

        mission_id = mission_queue[0].get("id")

        url = f"mission_queue/{mission_id}"
        self.receive_response(url, True, "Mission details: ")

        url = f"missions/{mission_guid}/actions"
        self.receive_response(url, True, "Action details: ")

    def cancel_mission_in_queue(self, mission_name: str) -> None:
        """
        Abort the given mission name from the current queue if found.

        Args:
            mission_name (str): The name of the mission to search and cancel.

        Returns:
            None
        """
        search = {
            "filters": [{"fieldname": "name", "operator": "=", "value": mission_name}]
        }
        mission = self.receive_response("missions", False, None, search)

        if not mission:
            return

        mission_id = mission[0].get("guid")
        search = {
            "filters": [
                {"fieldname": "mission_id", "operator": "=", "value": mission_id},
                {
                    "fieldname": "id",
                    "operator": ">",
                    "value": self.curr_mission_queue_id,
                },
            ]
        }

        mission_queue = self.receive_response("mission_queue", False, None, search)

        if not mission_queue:
            return

        mission_id = mission_queue[0].get("id")

        url = f"mission_queue/{mission_id}"
        self.delete(url)

    def find_act_type(self, action_type: str) -> dict:
        """
        Retrieve parameter details for a given action type.

        Args:
            action_type (str): The type of action for which to retrieve parameters.

        Returns:
            dict: A dictionary of parameters for the specified action type.
        """
        return self.action_dict.get(action_type, {}).get("parameters", {})

    def init_mission(
        self, mission_name: str, description: str, printq: bool = False
    ) -> dict:
        """
        Initialize a new mission with the given name and description.

        Args:
            mission_name (str): The name of the new mission.
            description (str): A description of the new mission.
            printq (bool): If True, print the response. Defaults to False.

        Returns:
            dict: The response from the MiR base after initializing the mission.
        """

        mission_data = {
            "description": description,
            "group_id": self.group_id,
            "name": mission_name,
        }

        return self.send_command(
            "missions", mission_data, printq, "New mission successfully added"
        )

    def init_action(
        self, act_param_dict: list, mission_id: str, priority: int, printq: bool = False
    ) -> None:
        """
        Initialize actions with default values for a new mission.

        Args:
            act_param_dict (list of dict): List of dictionaries where each dictionary contains action types and their parameters.
            mission_id (str): The ID of the mission to which actions are being added.
            priority (int): Priority level for the actions.
            printq (bool): If True, print the response. Defaults to False.

        Returns:
            None
        """
        for action_params in act_param_dict:
            action_type = next(iter(action_params.keys()))
            parameters = self.find_act_type(action_type)

            action_payload = {
                "action_type": action_type,
                "parameters": parameters,
                "id": mission_id,
                "priority": priority,
            }

            url = f"missions/{mission_id}/actions"
            self.send_command(
                url, action_payload, printq, "New action successfully added."
            )

    def set_action_params(
        self, mission_id: str, act_param_dict: list, printq: bool = False
    ) -> None:
        """
        Modify action parameters for a mission.

        Args:
            mission_id (str): The ID of the mission to modify actions for.
            act_param_dict (list of dict): List of dictionaries where each dictionary contains action types and their updated parameters.
            printq (bool): If True, print the response. Defaults to False.

        Returns:
            None
        """
        url = f"missions/{mission_id}/actions"
        actions = self.receive_response(url, printq)

        for action in actions:
            params = action.get("parameters", [])
            action_type = action.get("action_type")
            action_id = action.get("guid")

            if action_type != next(iter(act_param_dict[0].keys())):
                raise ValueError("Action type mismatch.")

            cur_dict = act_param_dict.pop(0).get(action_type, {})

            for k, v in cur_dict.items():
                for param in params:
                    if param["id"] == k or param["input_name"] == k:
                        param["value"] = v

            mission_actions = {
                "parameters": params,
                "priority": 1,
                "scope_reference": None,
            }

            url = f"missions/{mission_id}/actions/{action_id}"
            self.change_command(
                url, mission_actions, printq, "Action successfully changed."
            )

    def post_mission_to_queue(
        self,
        mission_name: str,
        act_param_dict: list,
        description: str = "",
        priority: int = 0,
        printq: bool = False,
    ) -> dict:
        """
        Post a mission to the queue. Creates a new mission if it doesn't exist, otherwise updates the existing mission.
        Initializes and modifies actions as specified and adds the mission to the queue.

        Args:
            mission_name (str): The name of the mission.
            act_param_dict (list of dict): List of dictionaries where each dictionary contains action types and their updated parameters.
            description (str): Description of the mission. Defaults to an empty string.
            priority (int): Priority level when posting the mission to the queue. Defaults to 1.
            printq (bool): If True, print the response. Defaults to False.

        Returns:
            dict: Response from the MiR base after posting the mission to the queue.
        """
        search = {
            "filters": [{"fieldname": "name", "operator": "=", "value": mission_name}]
        }
        mission = self.receive_response("missions", False, None, search)

        if not mission:
            mission = self.init_mission(mission_name, description, printq)
            mission_id = mission.get("guid")
            self.init_action(act_param_dict, mission_id, priority, printq)
        else:
            mission_id = mission[0].get("guid")

        self.set_action_params(mission_id, act_param_dict, printq)

        mission_queue_payload = {"mission_id": mission_id, "priority": priority}
        return self.send_command(
            "mission_queue",
            mission_queue_payload,
            printq,
            "Mission successfully added to queue.",
        )

    def wait_until_finished(self) -> None:
        """
        Continuously checks previously index mission to be done executing. Breaks out of loop once state is achieved.
        Prevents further missions or actions being sent if desired, since "Executing" != BUSY.
        """
        self.status = "BUSY"
        mission_finished = self.get_mission_queue()[-1]["state"]
        while mission_finished != "Done":
            mission_finished = self.get_mission_queue()[-1]["state"]
            time.sleep(5)
        self.status = "IDLE"

    def check_queue_completion(self, printq: bool = False) -> None:
        """
        Check and print the status of the current mission queue and its actions.

        This function retrieves the current mission queue, displays the completion status of the queue,
        and then retrieves and displays the actions for the current mission, showing their completion status.

        Returns:
            None
        """
        mission_queue = self.get_mission_queue()

        if not mission_queue:
            return

        current_mission = [m for m in mission_queue if m["state"] == "Executing"]

        if current_mission:
            miss_id = current_mission[0].get("id")
            mission_guid = self.receive_response("mission_queue/" + str(miss_id)).get(
                "mission_id"
            )
            mission_name = self.receive_response("missions/" + mission_guid).get("name")

            if printq:
                self.find_mission_in_queue(mission_name)

    def self_status(self) -> dict:
        """
        Retrieves the current system status of the MiR Robotic base.

        Returns:
            dict: The system status information.
        """
        return self.receive_response("status", True)

    def get_user_group_id(self) -> str:
        """
        Retrieves the ID of the first mission group.

        This ID is necessary when posting or creating a mission. Can be modified if a different mission group is desired.

        Returns:
            str: The ID of the first mission group.
        """
        get_id = self.receive_response("mission_groups", False)
        return get_id[0].get("guid")

    def receive_response(self, endpoint: str, search: Optional[dict] = None) -> dict:
        """
        Sends a GET or POST request to the MiR API and handles the response. POST requests are modified GET requests with search payloads to filter the response.

        Args:
            endpoint (str): The API endpoint to query.
            printq (bool): Whether to print the response details.
            message (str): An optional message to print if the request is successful.
            search (dict): An optional search payload for POST requests.

        Returns:
            dict: The parsed JSON response from the API.

        Raises:
            ValueError: If the API request fails.
        """
        if search is not None:
            url = f"{endpoint}/search"
            response = requests.post(
                f"{self.host}{url}", json=search, headers=self.headers, timeout=5
            )
        else:
            response = requests.get(
                f"{self.host}{endpoint}", headers=self.headers, timeout=5
            )

        text = json.loads(response.text)
        status = response.status_code

        if status in {200, 201}:
            return text
        raise ValueError(f"Error sending GET request: {text} (Status code: {status})")

    def send_command(self, endpoint: str, body: dict) -> dict:
        """
        Sends a POST request to the MiR API and handles the response.

        Args:
            endpoint (str): The API endpoint to post data to.
            body (dict): The JSON payload to send in the request.

        Returns:
            dict: The parsed JSON response from the API.

        Raises:
            ValueError: If the API request fails.
        """
        response = requests.post(
            f"{self.host}{endpoint}", json=body, headers=self.headers, timeout=5
        )
        text = json.loads(response.text)
        status = response.status_code

        if status == 201:
            return text
        raise ValueError(f"Error sending POST request: {text} (Status code: {status})")

    def change_command(self, endpoint: str, body: dict) -> dict:
        """
        Sends a PUT request to the MiR API to update data and handles the response.

        Args:
            endpoint (str): The API endpoint to update data at.
            body (dict): The JSON payload to send in the request.

        Returns:
            dict: The parsed JSON response from the API.

        Raises:
            ValueError: If the API request fails.
        """
        response = requests.put(
            f"{self.host}{endpoint}", json=body, headers=self.headers, timeout=5
        )
        text = json.loads(response.text)
        status = response.status_code

        if status in {200, 201}:
            return text
        raise ValueError(f"Error sending PUT request: {text} (Status code: {status})")

    def delete(self, endpoint: str) -> str:
        """
        Sends a DELETE request to the MiR API and handles the response.

        Args:
            endpoint (str): The API endpoint to delete data from.
            printq (bool): Whether to print the response details.
            message (str): An optional message to print if the request is successful.

        Returns:
            str: The response text from the API.

        Raises:
            ValueError: If the API request fails.
        """
        response = requests.delete(
            f"{self.host}{endpoint}", headers=self.headers, timeout=5
        )
        text = response.text
        status = response.status_code

        if status == 204:
            return text
        raise ValueError(
            f"Error sending DELETE request: {text} (Status code: {status})"
        )

    def create_action_dict(self) -> None:
        """
        Creates a dictionary with default parameters for various action types used in missions.

        Returns:
            dict: A dictionary containing default parameter values for action types such as 'relative_move', 'move_to_position', 'move', and 'docking'.
        """
        return {
            "relative_move": {
                "parameters": [
                    {"id": "x", "input_name": None, "value": 0.0},
                    {"id": "y", "input_name": None, "value": 0.0},
                    {"id": "orientation", "input_name": None, "value": 0.0},
                    {"id": "max_linear_speed", "input_name": None, "value": 0.25},
                    {"id": "max_angular_speed", "input_name": None, "value": 0.25},
                    {"id": "collision_detection", "input_name": None, "value": True},
                ]
            },
            "move_to_position": {
                "parameters": [
                    {"id": "x", "input_name": None, "value": 0.0},
                    {"id": "y", "input_name": None, "value": 0.0},
                    {"id": "orientation", "input_name": None, "value": 0.0},
                    {"id": "retries", "input_name": None, "value": 10},
                    {"id": "distance_threshold", "input_name": None, "value": 0.1},
                ]
            },
            "move": {
                "parameters": [
                    {
                        "id": "position",
                        "input_name": None,
                        "name": "another_move",
                        "value": "b34d6e54-5670-11ef-a572-0001297b4d50",
                    },
                    {
                        "id": "cart_entry_position",
                        "input_name": None,
                        "name": "Main",
                        "value": "main",
                    },
                    {
                        "id": "main_or_entry_position",
                        "input_name": None,
                        "name": "Main",
                        "value": "main",
                    },
                    {
                        "id": "marker_entry_position",
                        "input_name": None,
                        "name": "Entry",
                        "value": "entry",
                    },
                    {"id": "retries", "input_name": None, "value": 10},
                    {"id": "distance_threshold", "input_name": None, "value": 0.1},
                ]
            },
            "docking": {
                "parameters": [
                    {
                        "id": "marker",
                        "input_name": None,
                        "name": "camera_marker",
                        "value": "4ccacd0d-7f46-11ee-8521-0001297b4d50",
                    },
                    {
                        "id": "marker_type",
                        "input_name": None,
                        "name": "Narrow asymmetric MiR500/1000 shelf",
                        "value": "mirconst-guid-0000-0001-marker000001",
                    },
                    {"id": "retries", "input_name": None, "value": 10},
                    {"id": "max_linear_speed", "input_name": None, "value": 0.3},
                ]
            },
            "wait": {
                "parameters": [
                    {"id": "time", "input_name": None, "value": "00:00:05.000000"}
                ]
            },
        }

    def create_position_dict(self) -> None:
        """
        Creates a dictionary of positions from a map and saves it to a JSON file.

        The dictionary maps position names to their details, excluding those with 'entry' in their names.

        Returns:
            None
        """
        url = f"maps/{self.map_guid}/positions"
        map_positions = self.receive_response(url)
        position_dict = {}

        for position in map_positions:
            pos_id = position.get("guid")
            type_id = position.get("type_id")

            url = f"positions/{pos_id}?whitelist=pos_x,type_id,orientation,guid,pos_y"
            filtered = self.receive_response(url)

            url = f"positions/{pos_id}?whitelist=name"
            name = self.receive_response(url).get("name")

            url = f"position_types/{type_id}"
            position_type = self.receive_response(url)
            pos_name = position_type.get("name")

            if "entry" not in pos_name:
                position_dict[name] = filtered

        data = {self.map_name: position_dict}
        self.locations_dict = data

    def set_mission_queue_id(self) -> int:
        """
        Gets the ID of the last mission in the mission queue.

        Returns:
            int: The ID of the last mission in the queue.
        """
        mission_queue = self.receive_response("mission_queue")
        return mission_queue[-1].get("id")

    def get_state(self) -> str:
        """
        Retrieves the current state of the system.

        Returns:
            str: The current state of the system.
        """
        url = "status/?whitelist=state_text"
        state = self.receive_response(url, False).get("state_text")

        return state.upper()

    def move(self, location_name: str) -> dict:
        """
        Creates a mission to move to a specified location and adds it to the mission queue.

        Args:
            location (str): The location to move to.

        Returns:
            dict: The response from posting the mission to the queue.
        """
        mission_name = f"dock_to_{location_name}_{dt.datetime.now()}"

        guid = self.locations_dict[self.map_name][location_name]["guid"]
        return self.post_mission_to_queue(mission_name, [{"move": {"position": guid}}])

    def dock(self, location_name: str) -> dict:
        """
        Creates a mission to dock at a specified location and adds it to the mission queue.

        Args:
            location (str): The location to dock at.

        Returns:
            dict: The response from posting the mission to the queue.
        """
        mission_name = f"dock_to_{location_name}_{dt.datetime.now()}"

        guid = self.locations_dict[self.map_name][location_name]["guid"]
        return self.post_mission_to_queue(mission_name, [{"docking": {"marker": guid}}])

    def wait(self, delay_seconds: float) -> dict:
        """
        Creates a mission to wait for a specified time and adds it to the mission queue.

        Args:
            time (str): The amount of time to wait for.

        Returns:
            dict: The response from posting the mission to the queue.
        """
        time = str(dt.timedelta(seconds=delay_seconds))
        mission_name = f"wait_for_{time}_{dt.datetime.now()}"
        return self.post_mission_to_queue(mission_name, [{"wait": {"time": time}}])
