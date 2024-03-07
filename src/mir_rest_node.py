#! /usr/bin/env python3
"""The server for the PF400 robot that takes incoming WEI flow requests from the experiment application"""

import datetime
import json
import traceback
from argparse import ArgumentParser, Namespace
from contextlib import asynccontextmanager
from pathlib import Path
from time import sleep

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from wei.core.data_classes import (
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
)
from wei.helpers import extract_version


def parse_args() -> Namespace:
    """Parses the command line arguments for the PF400 REST node"""
    parser = ArgumentParser()
    parser.add_argument("--alias", type=str, help="Name of the Node", default="pf400")
    parser.add_argument("--host", type=str, help="Host for rest", default="0.0.0.0")
    parser.add_argument("--port", type=int, help="port value")
    return parser.parse_args()


global pf400_ip, pf400_port, state, action_start


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, parses the workcell argument
    Parameters
    ----------
    app : FastApi
       The REST API app being initialized

    Returns
    -------
    None"""
    global pf400, state, pf400_ip, pf400_port

    args = parse_args()
    pf400_ip = args.pf400_ip
    pf400_port = args.pf400_port

    try:
        pf400 = PF400(pf400_ip, pf400_port)
        pf400.initialize_robot()
        state = "IDLE"
    except Exception:
        state = "ERROR"
        traceback.print_exc()
    else:
        print("PF400 online")
    yield

    # Do any cleanup here
    pass


app = FastAPI(
    lifespan=lifespan,
)


def check_state():
    """Updates the MiR state

    Parameters:
    -----------
        None
    Returns
    -------
        None
    """
    pass


@app.get("/state")
def state():
    """Returns the current state of the Pf400 module"""
    global state, action_start
    if not (state == "BUSY") or (
        action_start
        and (datetime.datetime.now() - action_start > datetime.timedelta(0, 2))
    ):
        check_state()
    return JSONResponse(content={"State": state})


@app.get("/resources")
async def resources():
    """Returns info about the resources the module has access to"""
    global pf400
    return JSONResponse(content={"State": pf400.get_status()})


@app.get("/about")
async def about() -> JSONResponse:
    """Returns a description of the actions and resources the module supports"""
    global state
    about = ModuleAbout(
        name="Pf400 Robotic Arm",
        model="Precise Automation PF400",
        description="pf400 is a robot module that moves plates between two robot locations.",
        interface="wei_rest_node",
        version=extract_version(Path(__file__).parent.parent / "pyproject.toml"),
        actions=[
            ModuleAction(
                name="transfer",
                description="This action transfers a plate from a source robot location to a target robot location.",
                args=[
                    ModuleActionArg(
                        name="source",
                        description="Source location in the workcell for pf400 to grab plate from.",
                        type="str",
                        required=True,
                    ),
                ],
            ),
        ],
        resource_pools=[],
    )
    return JSONResponse(content=about.model_dump(mode="json"))


@app.post("/action")
def do_action(action_handle: str, action_vars: str):
    """Executes the action requested by the user"""
    response = {"action_response": "", "action_msg": "", "action_log": ""}
    print(action_vars)
    global pf400, state, action_start
    if state == "BUSY":
        return
    action_start = datetime.datetime.now()
    if state == "PF400 CONNECTION ERROR":
        response["action_response"] = "failed"
        response["action_log"] = "Connection error, cannot accept a job!"
        return response

    vars = json.loads(action_vars)

    err = False
    state = "BUSY"
    if action_handle == "mission":
        print("test_mission")
    else:
        msg = "UNKNOWN ACTION REQUEST! Available actions: mission"
        response["action_response"] = "failed"
        response["action_log"] = msg
        return response


if __name__ == "__main__":
    import uvicorn

    args = parse_args()

    uvicorn.run(
        "mirbase_rest_node:app",
        host=args.host,
        port=args.port,
        reload=True,
        ws_max_size=100000000000000000000000000000000000000,
    )
