#!/usr/bin/env python3
"""Driver code for the MiR 250 Robotic base."""


import requests
import json
import cmd

from requests.api import post
from pprint import pprint


class MiR_Base:
    """Main Driver Class for the MiR Robotic base."""

    def __init__(
        self,
        mir_ip="mirbase2.cels.anl.gov",
        mir_key="Basic RGlzdHJpYnV0b3I6NjJmMmYwZjFlZmYxMGQzMTUyYzk1ZjZmMDU5NjU3NmU0ODJiYjhlNDQ4MDY0MzNmNGNmOTI5NzkyODM0YjAxNA==",
        map_name=None,
        group_id=None,
        action_dict=None,
    ):
        """
        Description:
        """
        self.mir_ip = mir_ip
        self.mir_key = mir_key
        self.host = "http://" + self.mir_ip + "/api/v2.0.0/"

        # Formatting the headers.
        self.headers = {}
        self.headers["Content-Type"] = "application/json"
        self.headers["Authorization"] = self.mir_key

        ##
        self.map_name = map_name
        self.current_map = self.get_map()
        self.map_guid = self.current_map["guid"]
        self.group_id = self.get_user_group_id()
        self.action_dict = self.create_action_dict()

    def get_map(self):

        get_maps = requests.get(
            self.host + "maps",
            headers=self.headers
        )

        maps = json.loads(get_maps.text)
        if not maps:
            text = input("No maps created. Create new map? [y/n]: ") # WIP
            return text
        
        if not self.map_name:
            print("Current map not set, using first instance...")
        else:
            current_map = list(filter(lambda map: map['name'] == self.map_name, maps))
            if not current_map:
                current_map = maps[0]
        
        print("Current Map: ", current_map[0])

        return current_map[0]
    
    def test_record_new_map(self): # WIP
        return

    def get_actions(self, print=False):
        """
            get_action: Retrieves and prints all valid action types and their descriptions.
        """
        get_actions = requests.get(
            self.host + "actions",
            headers=self.headers,
        )

        all_actions = json.loads(get_actions.text)

        if print:
            pprint(all_actions)

        return all_actions

    def get_action_type(self, action_type=str, printq=False):
        """
            get_action_type: Retrieves and prints all actions and their descriptions for a given action type.
        """
        get_action_type = requests.get(
            self.host + "actions/" + action_type, 
            headers=self.headers)
        
        action_details = json.loads(get_action_type.text)

        if printq:
            pprint(action_details)

        return action_details
    
    def create_dashboard(self, name, id=None, fleet_dashboard=None, guid=None, print=False): 
        """
            create_dashboard: Creates new dashboard. Name must be provided, and should be unique.
        """
        assert name is not None, "Name must be provided for creating a dashboard."
        
        all_dashboards = self.get_dashboards()

        for dashboard in all_dashboards:
            assert name != dashboard['name'], "Dashboard name already exists."

        dashboard_json = {
            "name": name
        }

        if id is not None:
            dashboard_json["created_by_id"] = id
        if fleet_dashboard is not None:
            dashboard_json["fleet_dashboard"] = fleet_dashboard
        if guid is not None:
            dashboard_json["guid"] = guid
        
        dashboard = requests.post(self.host + "dashboards", json=dashboard_json, headers=self.headers)

        if print:
            pprint(dashboard.text)

        return
    
    def get_dashboards(self, print=False):
        """
            get_dashboards: Retrieves all current dashboards and prints information.
        """
        get_dashboards = requests.get(
            self.host + "dashboards",
            headers=self.headers,
        )
        all_dashboards = json.loads(get_dashboards.text)

        if print:
            pprint(all_dashboards)

        return all_dashboards
    
    def delete_dashboard(self, id=str):
        """
            delete_dashboard: Searches for dashboard under given dashboard name/guid, deletes if found.
        """
        all_dashboards = self.get_dashboards()

        for dashboard in all_dashboards:
            if id == dashboard['name'] or id == dashboard['guid']:
                response = requests.delete(
                    self.host + "dashboards/" + dashboard['guid'],
                    headers=self.headers
                )
                print(f"Dashboard '{id}' successfully deleted.")
                break
        else:
            raise ValueError(f"Dashboard '{id}' not found.")
        
        return
        
    def list_missions(self, print=False):

        get_missions = requests.get(self.host + "missions", headers=self.headers)
        all_missions = json.loads(get_missions.text)

        if print == True:
            pprint(all_missions) # *** Print them nicely.

        return all_missions
    
    def get_mission_queue(self, print=False):

        mission_queue = requests.get(
            self.host + "mission_queue",
            headers=self.headers
        )

        if mission_queue.status_code == 200:
            if print==True:
                pprint(json.loads(mission_queue.text)) # Print nicely?
        elif mission_queue.status_code == 404 or mission_queue.status_code == 410:
            print("Error: No current mission queue found.")

        return mission_queue.text

    def get_mission_queue_actions(self, print=False):

        mission_queue = requests.get(
            self.host + "mission_queue",
            headers=self.headers
        )

        if mission_queue.status_code == 200:
            if print==True:
                pprint(json.loads(mission_queue.text)) # Print nicely?
        elif mission_queue.status_code == 404 or mission_queue.status_code == 410:
            print("Error: No current mission queue found.")

        return mission_queue.text
    
    def delete_mission_queue(self):

        response = requests.delete(
            self.host + "mission_queue",
            headers=self.headers
        )

        if response.status_code == 204:
            print("Success, mission queue emptied.")
        
        return response
    
    def find_mission_in_queue(self, mission_name):

        all_missions = self.list_missions()

        for i in range(len(all_missions)):
            if mission_name == all_missions[i]["name"]:
                temp_id = all_missions[i]["guid"]
                details = requests.get(
                    self.host + "mission_queue/" + temp_id + "/actions",
                    headers=self.headers
                )
                mission = requests.get(
                    self.host + "mission_queue/" + temp_id,
                    headers=self.headers
                )

                print("Mission Details: \n") # *** Print nicely? More human-readable?
                pprint(json.loads(mission.text))
                print("Mission Actions: \n")
                pprint(json.loads(details.text))

                return
            
        print("Mission name not found in mission queue. Current queue: \n")
        self.get_mission_queue()
        # text = input("Add current mission name to queue? [y/n]: \n")
        # if text.lower() == "y":
        #     self.post_mission_to_queue(mission_name)
        #     return
        
        return
    
    def delete_mission_in_queue(self, mission_name):

        all_missions = self.list_missions()

        for i in range(len(all_missions)):
            if mission_name == all_missions[i]["name"]:
                temp_id = all_missions[i]["guid"]
                response = requests.delete(
                    self.host + "mission_queue/" + temp_id,
                    headers=self.headers
                )

                if response.status_code == 204:
                    print("Mission successfully deleted from queue.")

                return
            
        print("Mission name not found in mission queue. Current queue: \n")
        self.get_mission_queue()
        
        return
    
    def find_act_type(self, action_type):
        
        actions = self.action_dict
        parameters = actions.get(action_type)["parameters"]
        
        return parameters
    
    def init_mission(self, mission_name, description, printq=False):

        Missions = {
                "description" : description,
                "group_id" : self.group_id,
                "name" : mission_name
            }

        response = requests.post(
            self.host + "missions", 
            json=Missions,
            headers=self.headers
        )

        if response.status_code == 201:
            print("New mission successfully added.")
            if printq==True:
                pprint(json.loads(response.text))
        else:
            print("Error adding a new mission: ", response.status_code, response.text)

        return response
    
    def init_action(self, act_param_dict, mission_id, priority, printq=False):
        
        for i in range(len(act_param_dict)):
            action_type = list(act_param_dict[i].keys())[0]
            parameters = self.find_act_type(action_type)

            action_payload = {
                "action_type" : action_type,
                "parameters" : parameters,
                "id" : mission_id,
                "priority" : priority
                }
            
            response = requests.post(
                    self.host + "missions/" + mission_id + "/actions",
                    json=action_payload,
                    headers=self.headers
                )
            
            if response.status_code == 201:
                print("New action successfully added.")
                if printq:
                    pprint(json.loads(response.text))
            else:
                print("Error adding a new action: ", response.status_code, response.text)
        
        return 
    
    def set_action_params(self, mission_id, act_param_dict):

        response = requests.get(
            self.host + "missions/" + mission_id + "/actions",
            headers=self.headers
        )

        actions = json.loads(response.text)
        parameters = []

        for action in actions:
            params = action.get("parameters")
            action_type = action.get("action_type")
            for act_dict in act_param_dict[:]:
                if action_type in act_dict:
                    params_dict = act_dict.pop(action_type)
                    for k, v in params_dict.items():
                        for param in params:
                            if param['id'] == k or param['input_name'] == k:
                                param['value'] = v
                    for p in params:
                        parameters.append(p)
                    break
        print(parameters)
        return parameters

    # def set_action_params(self, mission_id, act_param_dict):
    #     response = requests.get(
    #         self.host + "missions/" + mission_id + "/actions",
    #         headers=self.headers
    #     )

    #     actions = json.loads(response.text)

    #     for action in actions:
    #         action_type = action.get("action_type")
    #         if action_type in act_param_dict:
    #             param_updates = act_param_dict[action_type]
    #             for param in action.get("parameters", []):
    #                 param_id = param.get("id")
    #                 if param_id in param_updates:
    #                     param["value"] = param_updates[param_id]
    #             del act_param_dict[action_type]  # Remove the matched action type

    #     pprint(actions)
    #     return actions

    
    def post_mission_to_queue(self, mission_name, act_param_dict, description="", priority=1, printq=False):

        all_missions = self.list_missions()

        if len(act_param_dict) < 2: # TBD, only works with single actions.
            action_type = list(act_param_dict[0].keys())[0] # Access first key of first dictionary in list.

        mission_id = None

        for mission in all_missions:
            if mission["name"] == mission_name:
                mission_id = mission["guid"]
        
        if mission_id == None: # Change back later
            
            mission = self.init_mission(mission_name, description, printq)
            mission_det = json.loads(mission.text)

            mission_id = mission_det.get("guid")

            actions = self.init_action(act_param_dict, mission_id, priority, printq)

        params = self.set_action_params(mission_id, act_param_dict)

        Mission_queues = {
                    "mission_id" : mission_id,
                    "parameters" : params,
                    "priority" : priority
                }
            
        response = requests.post(
            self.host + "mission_queue",
            json=Mission_queues,
            headers=self.headers
        )
        
        if response.status_code == 201:
            print("Mission successfully added to queue!")
            if printq:
                pprint(json.loads(response.text))
        else:
            print("Error posting mission to queue: ", response.status_code, response.text)
        
        return response

    def check_queue_completion(self):

        mission_queue = self.get_mission_queue()
        width = 50

        print("Current Mission Queue: \n")
        for i in range(len(mission_queue)):
            print(mission_queue[i]["name"] + ": " + mission_queue[i]["state"] + "\n")
            if mission_queue[i]["state"] == "Pending":
                cur_mission = mission_queue[i]
                index = i + 1

        percent = (index/len(mission_queue)) * 100
        bar_length = int(width*(index/len(mission_queue)))
        bar = '#' * bar_length + '-' * (width - bar_length)
        print(f"\r[{bar}] {percent:6.2f}%  Queue Complete\n")

        print("Current Mission: " + cur_mission["name"] + "\n")

        action_queue = requests.get(
           self.host + "mission_queue/" + cur_mission["guid"] + "/actions",
           headers=self.headers 
        )

        action_details = action_queue.text

        print("Current Mission Actions: \n")
        for i in range(len(action_details)):
            print(action_details[i]["action_type"] + ": " + action_details[i]["state"] + "\n")
            if action_details[i]["state"] == "Pending":
                cur_action = action_details[i]
                index = i + 1

        percent = (index/len(action_details)) * 100
        bar_length = int(width*(index/len(action_details)))
        bar = '#' * bar_length + '-' * (width - bar_length)
        print(f"\r[{bar}] {percent:6.2f}% Mission Complete\n")

        print("Current Action: " + cur_action["action_type"] + "\n")

        return

    def status(self):

        get_status = requests.get(
            self.host + "status",
            headers=self.headers,
        )
        pprint(json.loads(get_status.text))

        return json.loads(get_status.text)
    
    def get_user_group_id(self):

        get_id = requests.get(
            self.host + "mission_groups",
            headers=self.headers,
        )

        users = json.loads(get_id.text)

        return users[0].get("guid")
    
    def create_action_dict(self):

        action_dict = {
            "relative_move" : {
                "parameters" : [
                    {
                        'id' : 'x',
                        'input_name' : 'X',
                        'value' : 0.0
                    },
                    {
                        'id' : 'y',
                        'input_name' : 'Y',
                        'value' : 0.0
                    },
                    {
                        'id' : 'orientation',
                        'input_name' : 'Orientation',
                        'value' : 0.0
                    },
                    {
                        'id' : 'max_linear_speed',
                        'input_name' : 'Maximum linear speed',
                        'value' : 0.25
                    },
                    {
                        'id' : 'max_angular_speed',
                        'input_name' : 'Maximum angular speed',
                        'value' : 0.25
                    },
                    {
                        'id' : 'collision_detection',
                        'input_name' : 'Collision detection',
                        'value' : True
                    }
                ]
            },
            "move_to_position" : {
                "parameters" : [
                    {
                        'id' : 'x',
                        'input_name' : 'X',
                        'value' : 0.0
                    },
                    {
                        'id' : 'y',
                        'input_name' : 'Y',
                        'value' : 0.0
                    },
                    {
                        'id' : 'orientation',
                        'input_name' : 'Orientation',
                        'value' : 0.0
                    },
                    {
                        'id' : 'retries',
                        'input_name' : 'Retries (Blocked Path)',
                        'value' : 10
                    },
                    {
                        'id' : 'distance_threshold',
                        'input_name' : 'Distance threshold',
                        'value' : 0.1
                    }
                ]
            },
            "move" : { # Populate with default values.. Check with own positions, can automate. WIP
                "parameters" : [
                    {
                        'id' : 'position',
                        'input_name' : 'Position',
                        'name': 'test_pos',
                        'value': '88c7d8ff-54d0-11ef-90e0-0001297b4d50' 
                    },
                    {
                        'id' : 'cart_entry_position',
                        'input_name' : 'Cart position',
                        'name' : 'Main',
                        'value' : 'main'
                    },
                    {
                        'id' : 'main_or_entry_position',
                        'input_name' : 'Position type',
                        'name' : 'Main',
                        'value' : 'main'
                    },
                    {
                        'id' : 'marker_entry_position',
                        'input_name' : 'Position type',
                        'name' : 'Entry',
                        'value' : 'entry'
                    },
                    {
                        'id' : 'retries',
                        'input_name' : 'Retries (Blocked Path)',
                        'value' : 10
                    },
                    {
                        'id' : 'distance_threshold',
                        'input_name' : 'Distance threshold',
                        'value' : 0.1
                    }
                ]
            },
            "docking" : {
                "parameters" : [
                    {
                        'id' : 'marker',
                        'input_name' : 'Marker position',
                        'name' : 'camera_marker',
                        'value' : '4ccacd0d-7f46-11ee-8521-0001297b4d50'
                    },
                    {
                        'id' : 'marker_type',
                        'input_name' : 'Marker_type',
                        'name' : 'Narrow asymmetric MiR500/1000 shelf', # ??
                        'value' : 'mirconst-guid-0000-0001-marker000001'
                    },
                    {
                        'id' : 'retries',
                        'input_name' : 'Retries (Blocked Path)',
                        'value' : 10
                    },
                    {
                        'id' : 'max_linear_speed',
                        'input_name' : 'Maximum linear speed',
                        'value' : 0.1
                    }
                ]  
            }
        }

        return action_dict



if __name__ == "__main__":
    mir_base = MiR_Base(map_name="RPL")

    # response = mir_base.get_action_type("prompt_user", True)
    # response = mir_base.get_action_type("adjust_localization", True)
    # response = mir_base.get_action_type("if", True)
    # response = mir_base.get_action_type("pause", True)
    # response = mir_base.get_action_type("reduce_protective_fields", True)
    # response = mir_base.get_action_type("create_autolog", True)
    # response = mir_base.get_action_type("return", True)
    # response = mir_base.get_action_type("check_pose", True)
    # response = mir_base.get_action_type("throw_error", True)
    # response = mir_base.get_action_type("wait", True)
    # response = mir_base.get_action_type("break", True)
    # response = mir_base.get_action_type("run_ur_program", True)
    # response = mir_base.get_action_type("try_catch", True)
    # response = mir_base.get_action_type("charging", True)
    # response = mir_base.get_action_type("while", True)
    # response = mir_base.get_action_type("continue", True)
    # response = mir_base.get_action_type("set_footprint", True)
    #response = mir_base.get_action_type("move", True)
    mir_base.post_mission_to_queue("testing_8.8.1.46", [{"move" : {"position" : "88c7d8ff-54d0-11ef-90e0-0001297b4d50"}}, {"move" : {"position" : "d99494c0-54d5-11ef-be3f-0001297b4d50"}}], "testing", 1, True)
    #, {"move" : {"position" : "88c7d8ff-54d0-11ef-90e0-0001297b4d50"}}]d99494c0-54d5-11ef-be3f-0001297b4d50
    
