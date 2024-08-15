#!/usr/bin/env python3
"""Driver code for the MiR 250 Robotic base."""


import requests
import json
import cmd
import json

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
        position_dict=None,
        curr_mission_queue_id=None,
        filename=None
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
        self.filename = filename
        self.map_name = map_name
        self.current_map = self.get_map()
        self.map_guid = self.current_map["guid"]
        self.group_id = self.get_user_group_id()
        self.action_dict = self.create_action_dict()
        self.position_dict = self.create_position_dict()
        self.curr_mission_queue_id = self.set_mission_queue_id()

    def get_map(self): # Works, not refined.

        maps = self.receive_response("maps")
        
        if not self.map_name:

            print("Current map not set, using first instance...")

        else:

            current_map = list(filter(lambda map: map['name'] == self.map_name, maps))

            if not current_map:

                current_map = maps[0]
        
        print("Current Map: ", current_map[0])

        return current_map[0]
    

    def get_actions(self, printq=False): # Works, refined.
        """
            get_actions: Retrieves and prints all valid action types and their descriptions.
        """

        actions = self.receive_response("actions", printq)

        return actions

    def get_action_type(self, action_type=str, printq=False): # Works, refined.
        """
            get_action_type: Retrieves and prints action parameters for a given action type.
        """

        url = "actions/" + action_type
        action_params = self.receive_response(url, printq)

        return action_params
        
    def list_missions(self, printq=False): # Works, refined.
        '''
            list_mission : Lists all created missions for the MiR.
        '''

        all_missions = self.receive_response("missions", printq)

        return all_missions
    
    def get_mission_queue(self, printq=False): # Works, refined.
        '''
            get_mission_queue : Prints all missions in the queue since the last mission queue id.
        '''
        search = {
            "filters" : [{
                "fieldname" : "id",
                "operator" : ">",
                "value" : self.curr_mission_queue_id
            }]}

        mission_queue = self.receive_response("mission_queue", printq, None, True, search)
        if len(mission_queue) < 1:
            print("No missions posted to queue since last session.")
            return

        return mission_queue
    
    def abort_mission_queue(self): # Works, refined.
        '''
            abort_mission_queue : Aborts all pending and executing missions in the mission queue.
        '''

        response = self.delete("mission_queue", False, "All missions aborted.")
        
        return response
    
    def clear_mission_queue(self):

        self.curr_mission_queue_id = self.set_mission_queue_id()

        return self.curr_mission_queue_id
    
    def find_mission_in_queue(self, mission_name): # Works, refined.
        '''
            find_mission_in_queue : Prints mission and action details for given mission name in queue.
        '''
        search = {"filters" : [{"fieldname" : "name","operator" : "=","value" : mission_name}]}
        mission = self.receive_response("missions", False, None, search)

        if len(mission) < 1:
            print("No existing mission found under that name.")
            return
        
        mission_id = mission[0].get("guid")
        search = {"filters" : [{"fieldname" : "mission_id","operator" : "=","value" : mission_id},{"fieldname" : "id","operator" : ">","value" : self.curr_mission_queue_id}]}
        
        mission = self.receive_response("mission_queue", False, None, search)

        if len(mission) < 1:
            print("No existing mission found under that name in the current queue.")
            return
        
        mission_id = mission[0].get("id")
 
        url = "mission_queue/" + str(mission_id)
        mission_details = self.receive_response(url, True, "Mission details: ")

        url = "mission_queue/" + str(mission_id) + "/actions"
        action_details = self.receive_response(url, True, "Action details: ")

        return
    
    def cancel_mission_in_queue(self, mission_name):
        '''
            cancel_mission_in_queue : Aborts  given mission name from current queue if found.
        '''
        search = {"filters" : [{"fieldname" : "name", "operator" : "=", "value" : mission_name}]}
        mission = self.receive_response("missions", False, None, search)

        if len(mission) < 1:
            print("No existing mission found under that name.")
            return
        
        mission_id = mission[0].get("guid")
        search = {"filters" : [{"fieldname" : "mission_id","operator" : "=","value" : mission_id},{"fieldname" : "id","operator" : ">","value" : self.curr_mission_queue_id}]}
        
        mission = self.receive_response("mission_queue", False, None, search)

        if len(mission) < 1:
            print("No existing mission found under that name in the current queue.")
            return
        
        mission_id = mission[0].get("id")
 
        url = "mission_queue/" + str(mission_id)
        response = self.delete(url)
        
        return
    
    def find_act_type(self, action_type): # Works.
        '''
            find_act_type : Returns parameter details for a given action type.
        '''
        
        actions = self.action_dict
        parameters = actions.get(action_type)["parameters"]
        
        return parameters
    
    def init_mission(self, mission_name, description, printq=False):
        '''
            init_mission : Helper function initializing new mission.
        '''

        Missions = {"description" : description,"group_id" : self.group_id,"name" : mission_name}

        response = self.send_command("missions", Missions, printq, "New mission successfully added")

        return response
    
    def init_action(self, act_param_dict, mission_id, priority, printq=False):
        '''
            init_action : Helper function initializing actions with default values when creating a new mission.
        '''
        
        for i in range(len(act_param_dict)):

            action_type = list(act_param_dict[i].keys())[0]
            parameters = self.find_act_type(action_type)

            action_payload = {
                "action_type" : action_type,
                "parameters" : parameters,
                "id" : mission_id,
                "priority" : priority
                }
            
            url = "missions/" + mission_id + "/actions"
            response = self.send_command(url, action_payload, printq, "New action successfully added.")

        return 
    
    def set_action_params(self, mission_id, act_param_dict, printq):
        '''
            set_action_params : Helper function to modify action parameters for a mission.
        '''

        url = "missions/" + mission_id + "/actions"
        actions = self.receive_response(url, printq)

        for action in actions:

            params = action.get("parameters")
            action_type = action.get("action_type")
            action_id = action.get("guid")

            if action_type != list(act_param_dict[0].keys())[0]:
                raise ValueError("Wrong")

            cur_dict = act_param_dict.pop(0).get(action_type)
            
            for k, v in cur_dict.items():
                for param in params:
                    if param['id'] == k or param['input_name'] == k:
                            param['value'] = v
            
            PutMission_action = {"parameters" : params,"priority" : 1,"scope_reference" : None}       

            url = "missions/" + mission_id + "/actions/" + action_id
            change_action = self.change_command(url, PutMission_action, printq, "Action successfully changed.")
        
        return 

    
    def post_mission_to_queue(self, mission_name, act_param_dict, description="", priority=1, printq=False):
        '''
            post_mission_to_queue: Checks if the mission name exists, if not, initializes the mission and actions with default values, then modifies the actions with the new parameters
            and posts the mission to queue.
                'mission_name' : Name to post mission under. If unique, creates new mission, if not, modifies existing mission.
                'act_param_dict' : List of dictionaries, where each dictionary takes the form of:
                    {<action_type> : 
                        {<parameter id : <new value>,
                        ...
                    }}
                    Actions must be given in the same order as when the mission was created. Only include parameter ids that you wish to change, others do not have to be specified.
                'description' : Enter a description for the mission if desired, otherwise blank.
                'priority' : Assign a priority when posting the mission to queue, otherwise 1.
                'printq' : Print all mission and action details throughout the process.
        '''

        search = {"filters" : [{"fieldname" : "name","operator" : "=","value" : mission_name}]}
        mission = self.receive_response("missions", False, None, search)

        if len(mission) < 1: 
            
            mission = self.init_mission(mission_name, description, printq)

            mission_id = mission.get("guid")

            actions = self.init_action(act_param_dict, mission_id, priority, printq)
        else:
            mission_id = mission[0].get("guid")

        params = self.set_action_params(mission_id, act_param_dict, printq)

        Mission_queues = {"mission_id" : mission_id,"priority" : priority}
        
        response = self.send_command("mission_queue", Mission_queues, printq, "Mission successfully added to queue.")
        
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
        '''
            status : Retrieves MiR system status.
        '''
        self_status = self.receive_response("status", True)

        return self_status
    
    def get_mission_actions_by_index(self, index):
        '''
            get_mission_actions_by_index : Retrieves mission and corresponding action details for the mission at the given index, for debugging.
        '''

        mission_details = self.receive_response("missions", False)
        mission_id = mission_details[index].get("guid")
        
        url = "missions/" + mission_id + "/actions"
        actions = self.receive_response(url, True) 

        return actions
    
    def get_user_group_id(self):
        '''
            get_user_group_id : Gets first mission group id, necessary when posting/creating a mission. Can be modified if different mission group desired.
        '''

        get_id = self.receive_response("mission_groups", False)
        id = get_id[0].get("guid")

        return id
    
    def receive_response(self, get, printq=False, message=None, search=None):

        if search!=None:

            get = get + "/search"
            body = search

            response = requests.post(
                self.host + get,
                json=body,
                headers=self.headers
            )

        else: 

            url = get
            response = requests.get(
                self.host + url,
                headers=self.headers
            )
        

        text = json.loads(response.text)
        status = response.status_code

        if status == 200 or status == 201:
            if message != None:
                print(message)
            if printq:
                pprint(text)
        else:
            raise ValueError("Error sending GET request: ", text, status)
        
        return text
    
    def send_command(self, post, body, printq=False, message=None):

        url = post
        command = requests.post(
            self.host + url,
            json=body,
            headers=self.headers
        )

        text = json.loads(command.text)
        status = command.status_code

        if status == 201:
            if message != None:
                print(message)
            if printq:
                pprint(text)
        else:
            raise ValueError("Error sending POST request: ", text, status)
        
        return text
        
    def change_command(self, put, body, printq=False, message=None):

        url = put
        print(body)
        
        change = requests.put(
            self.host + url,
            json=body,
            headers=self.headers
        )

        text = json.loads(change.text)
        status = change.status_code

        if status == 200 or status == 201:
            if message != None:
                print(message)
            if printq:
                pprint(text)
        else:
            raise ValueError("Error sending PUT request: ", text, status)
        
        return text
        
    def delete(self, delete, printq=False, message=None):

        url = delete
        response = requests.delete(
            self.host + url,
            headers=self.headers
        )

        text = response.text
        status = response.status_code

        if status == 204:
            if message != None:
                print(message)
            if printq:
                pprint(text)
        else:
            raise ValueError("Error sending DELETE request: ", text, status)
        
        return text
    
    def create_action_dict(self):
        '''
            create_action_dict : Dictionary setting default parameters for useful action types.
                'id' : Parameter name, must be used when changing default value.
                'input_name' : Required parameter, set to None, otherwise will create a variable that cannot be changed/stacked with multiple actions.
                'value' : Contains default value for all parameters, remains default unless modified explicitly when posting a mission.
        '''

        action_dict = {
            "relative_move" : {
                "parameters" : [
                    {
                        'id' : 'x',
                        'input_name' : None,
                        'value' : 0.0
                    },
                    {
                        'id' : 'y',
                        'input_name' : None,
                        'value' : 0.0
                    },
                    {
                        'id' : 'orientation',
                        'input_name' : None,
                        'value' : 0.0
                    },
                    {
                        'id' : 'max_linear_speed',
                        'input_name' : None,
                        'value' : 0.25
                    },
                    {
                        'id' : 'max_angular_speed',
                        'input_name' : None,
                        'value' : 0.25
                    },
                    {
                        'id' : 'collision_detection',
                        'input_name' : None,
                        'value' : True
                    }
                ]
            },
            "move_to_position" : {
                "parameters" : [
                    {
                        'id' : 'x',
                        'input_name' : None,
                        'value' : 0.0
                    },
                    {
                        'id' : 'y',
                        'input_name' : None,
                        'value' : 0.0
                    },
                    {
                        'id' : 'orientation',
                        'input_name' : None,
                        'value' : 0.0
                    },
                    {
                        'id' : 'retries',
                        'input_name' : None,
                        'value' : 10
                    },
                    {
                        'id' : 'distance_threshold',
                        'input_name' : None,
                        'value' : 0.1
                    }
                ]
            },
            "move" : {
                "parameters" : [
                    {
                        'id' : 'position',
                        'input_name' : None,
                        'name': 'another_move',
                        'value': 'b34d6e54-5670-11ef-a572-0001297b4d50' 
                    },
                    {
                        'id' : 'cart_entry_position',
                        'input_name' : None,
                        'name' : 'Main',
                        'value' : 'main'
                    },
                    {
                        'id' : 'main_or_entry_position',
                        'input_name' : None,
                        'name' : 'Main',
                        'value' : 'main'
                    },
                    {
                        'id' : 'marker_entry_position',
                        'input_name' : None,
                        'name' : 'Entry',
                        'value' : 'entry'
                    },
                    {
                        'id' : 'retries',
                        'input_name' : None,
                        'value' : 10
                    },
                    {
                        'id' : 'distance_threshold',
                        'input_name' : None,
                        'value' : 0.1
                    }
                ]
            },
            "docking" : {
                "parameters" : [
                    {
                        'id' : 'marker',
                        'input_name' : None,
                        'name' : 'camera_marker',
                        'value' : '4ccacd0d-7f46-11ee-8521-0001297b4d50'
                    },
                    {
                        'id' : 'marker_type',
                        'input_name' : None,
                        'name' : 'Narrow asymmetric MiR500/1000 shelf', 
                        'value' : 'mirconst-guid-0000-0001-marker000001'
                    },
                    {
                        'id' : 'retries',
                        'input_name' : None,
                        'value' : 10
                    },
                    {
                        'id' : 'max_linear_speed',
                        'input_name' : None,
                        'value' : 0.1
                    }
                ]  
            }
        }

        return action_dict

    def create_position_dict(self):

        url = "maps/" + self.map_guid + "/positions"
        map_positions = self.receive_response(url)
        position_dict = {}

        for position in map_positions:

            pos_id = position.get("guid")
            url = "positions/" + pos_id + "?whitelist=pos_x,type_id,orientation,guid,pos_y"
            filtered = self.receive_response(url)

            url = "positions/" + pos_id + "?whitelist=name"
            name = self.receive_response(url)

            position_dict[name.get("name")] = filtered
        
        data = {self.map_name : position_dict}
        filename = self.filename

        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

        return
    
    def set_mission_queue_id(self):

        mission_queue = self.receive_response("mission_queue")
        last_mission_id = mission_queue[-1].get("id")

        return last_mission_id
    
    def get_state(self):

        url = "status/?whitelist=state_text"
        state = self.receive_response(url, False)
        state = state.get("state_text")
        print(state.upper())

        return state.upper()
    
    def move(self, location):

        f = open(self.filename)
        data = json.load(f)
        guid = data[self.map_name][location]["guid"]
        move =self.post_mission_to_queue("move_to_"+location,[{"move": {"position":guid}}])

        return move
    
    def dock(self, location):

        f = open(self.filename)
        data = json.load(f)
        guid = data[self.map_name][location]["guid"]
        dock =self.post_mission_to_queue("dock_at_"+location,[{"docking": {"marker":guid}}], printq=True)

        return dock


if __name__ == "__main__":
    mir_base = MiR_Base(map_name="RPL", filename="locations.json")

    # response = requests.post(
    #     mir_base.host + "mission_queue/search",
    #     json = {
    #         "filters" : [{
    #             "fieldname" : "state",
    #             "operator" : "=",
    #             "value" : "Done"
    #         },{
    #             "fieldname" : "id",
    #             "operator" : ">",
    #             "value" : "5"
    #         }]
    #     },
    #     headers=mir_base.headers
    # )
    # print(response.text)

    # for i in range(5):
    #     mir_base.post_mission_to_queue("testing_8.14.01" + str(i), [{"move" : {"position" : "d99494c0-54d5-11ef-be3f-0001297b4d50"}}], "testing", 1, True)
    # mir_base.find_mission_in_queue("testing_8.14.011")

    #mir_base.post_mission_to_queue("testing_8.13.008", [{"move" : {"position" : "d99494c0-54d5-11ef-be3f-0001297b4d50"}},{"docking" : {"marker" : "f0908191-7f46-11ee-8521-0001297b4d50"}}], "testing", 1, True)
    # response = mir_base.get_info(-1)
    #y = mir_base.status()

    ## TESTING:

    # mir_base.get_actions(True)
    # mir_base.get_action_type("move", True)

    # mir_base.list_missions(True)

    # mir_base.get_mission_queue(True)
    # for i in range(5):
    #     mir_base.post_mission_to_queue("testing_8.14.01" + str(i), [{"move" : {"position" : "d99494c0-54d5-11ef-be3f-0001297b4d50"}}], "testing", 1, False)
    # for i in range(10):
    #     mir_base.get_mission_queue(True)

    # for i in range(5):
    #     mir_base.post_mission_to_queue("testing_8.14.01" + str(i), [{"move" : {"position" : "d99494c0-54d5-11ef-be3f-0001297b4d50"}}], "testing", 1, False)
    # mir_base.abort_mission_queue()
    # mir_base.get_mission_queue(True)

    # for i in range(5):
    #     mir_base.post_mission_to_queue("testing_8.14.01" + str(i), [{"move" : {"position" : "d99494c0-54d5-11ef-be3f-0001297b4d50"}}], "testing", 1, False)
    # mir_base.find_mission_in_queue("testing_8.14.011")

    #mir_base.post_mission_to_queue("testing_8.15.001", [{"move" : {"position" : "d99494c0-54d5-11ef-be3f-0001297b4d50"}}], "testing", 1, True)
    # mir_base.receive_response("positions", True)
    # mir_base.receive_response("missions/e4e2a4da-f71b-11ec-813f-0001297b4d50/actions", True)
    # mir_base.receive_response("positions/f0908191-7f46-11ee-8521-0001297b4d50", True)
    # mir_base.get_action_type("docking", True)
    
    # mir_base.post_mission_to_queue("test_dock", [{"docking" : {"marker" : "84c9b49f-3860-4ecb-8183-00515eebe186"}}], printq=True)
    # mir_base.get_action_type("docking", True)

    mir_base.move("test_move")
    mir_base.move("another_move")
    mir_base.move("charger1")

    
    
    


    
    
    
