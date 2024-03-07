#!/usr/bin/env python3
"""Driver code for the PF400 robot arm."""


import requests
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
    ):
        """
        Description:
        """
        self.mir_ip = mir_ip
        self.mir_key = mir_key
        self.host = "http://" + self.mir_ip + "/api/v2.0.0/"
        # format the headers
        self.headers = {}
        self.headers["Content-Type"] = "application/json"
        self.headers["Authorization"] = self.mir_key

        ##
        self.map_name = map_name
        self.current_map = self.get_map()
        self.map_guid = self.current_map["guid"]

    def get_map(self):
        get_maps = requests.get(self.host + "maps", headers=self.headers)
        maps = json.loads(get_maps.text)
        if not self.map_name:
            print("No map_name, using [0]")
        else:
            ## TODO: get case where map is not found
            current_map = list(filter(lambda map: map["name"] == self.map_name, maps))
            if not current_map:
                current_map = maps[0]
        print("Current Map:", current_map[0])
        return current_map[0]

    def get_positions(self):
        get_positions_by_map = requests.get(
            self.host + "maps/" + self.current_map["guid"] + "/positions",
            headers=self.headers,
        )
        positions = json.loads(get_positions_by_map.text)
        pprint(positions)
        return positions

    # def get_actions(self):
    #     get_actions = requests.get(
    #         self.host + "actions",
    #         headers=self.headers,
    #     )
    #     all_actions = json.loads(get_actions.text)
    #     pprint(all_actions)
    #     dets = requests.get(self.host + "actions/move", headers=self.headers)
    #     pprint(json.loads(dets.text))
    #     return all_actions

    def goto_positions(self, position=None):
        pass

    def list_missions(self):
        get_missions = requests.get(self.host + "missions", headers=self.headers)
        all_missions = json.loads(get_missions.text)
        return all_missions

    def run_mission(self):
        pass

    def post_mission(self, mission_name="", mission_vars=[]):
        """Function to use when you wish to post a mission to the queue
        Arguments:
            mission_name: the name you set in your Web Interface
        """
        all_missions = self.list_missions()
        for i in range(len(all_missions)):
            # print(all_missions[i]["name"])
            if all_missions[i]["name"] == mission_name:
                mission_id_temp = all_missions[i]["guid"]
                dets = requests.get(
                    self.host + "missions/" + mission_id_temp + "/actions",
                    headers=self.headers,
                )
                pprint(json.loads(dets.text))

                dets = requests.get(
                    self.host + "missions/" + mission_id_temp, headers=self.headers
                )
                pprint(json.loads(dets.text))

        mission_json = {"mission_id": mission_id_temp, "parameters": mission_vars}
        mission = requests.post(
            self.host + "mission_queue", json=mission_json, headers=self.headers
        )
        print(mission.text)

    def delete_mission():
        """delete all the missions"""
        return requests.delete(self.host + "mission_queue", headers=self.headers)

    def check_completion():
        """check whether all the missions in the queue has completed or not"""
        status = False
        while status is False:
            check_mission_status = requests.get(
                self.host + "mission_queue", headers=self.headers
            )
            response_native = json.loads(check_mission_status.text)
            status_string = response_native[-1]["state"]
            if status_string == "Done":
                status = True
            else:
                status = False


if __name__ == "__main__":
    mir_base = MiR_Base(map_name="RPL")
    # pprint(mir_base.list_missions())
    ### mir_base.get_actions()
    # mir_base.get_positions()
    mir_base.post_mission(mission_name="DockCharger1")
    # mir_base.post_mission(mission_name="GoToCamera")
    # mir_base.post_mission(mission_name="Move")
    # mir_base.post_mission(
    #     mission_name="GoToPositionPrototype",
    #     mission_vars=[
    #         {
    #             "x": 19.5,
    #             "y": 19.5,
    #             "orientation": 90.0,
    #             # "retries": 10,
    #             # "distance_threshold": 0.25,
    #         }
    #     ],
    # )
# https://mirbase2.cels.anl.gov/?x=10.1&y=19.5&orientation=-90.00&mode=map-go-to-coordinates
