from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import opendream
from .layer import Layer
from . import extension_loader
from typing import Any, Dict
import inspect
import requests

app = FastAPI()

# Add CORSMiddleware
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/operation/{op_name}")
async def serve(op_name: str, **payload: Dict[str, Any]) -> Dict[str, Any]:

    if op_name not in opendream.operators:
        raise HTTPException(status_code=400, detail=f"Operator {op_name} not found")
    
    # iterate over params, replace base64 images with PIL images
    for i, arg in enumerate(payload["payload"]["params"]):
        if isinstance(payload["payload"]["params"][i], str) and payload["payload"]["params"][i].startswith("data:image/png;base64,"):
            payload["payload"]["params"][i] = Layer.b64_to_layer(payload["payload"]["params"][i])
        
        associated_layer = opendream.CANVAS.get_layer(arg)
        if associated_layer is not None:
            payload["payload"]["params"][i] = associated_layer
            
    # iterate over kwargs, replace string ints with ints
    for key, value in payload["payload"]["options"].items():
        if isinstance(value, str) and value.isdigit():
            payload["payload"]["options"][key] = int(value)
        

    func = opendream.operators[op_name]
    try:
        # TODO: doesn't this mean we no longer need the define_op decorator?
        layer = opendream.define_op(func)(*payload["payload"]["params"], **payload["payload"]["options"])[-1]
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    return layer.serialize()

@app.get("/available_operations")
async def available_operations() -> Dict[str, Any]:
    excluded_operators = []
    to_return = {"operators": [op for op in opendream.operators if op not in excluded_operators]}
    
    return to_return

@app.post("/add_mask")
async def add_mask(payload: Dict[str, Any]) -> Dict[str, Any]:
    layer = Layer.b64_to_layer(payload["mask"])
    # currently we only support square masks (512 is a memory limit)
    # layer.resize(512, 512)
    layer.set_metadata({"op": "mask", "image": Layer.pil_to_b64(layer.get_image()) })
    opendream.CANVAS.add_layer(layer)
    return {"layer": layer.serialize()}

@app.post("/add_layer")
async def add_layer(payload: Dict[str, Any]) -> Dict[str, Any]:
    layer = Layer.b64_to_layer(payload["image"])
    # layer.resize(512, 512)
    layer.set_metadata({"op": "load_image", "image": Layer.pil_to_b64(layer.get_image())})
    opendream.CANVAS.add_layer(layer)
    return {"layers": opendream.CANVAS.get_serialized_layers(), "workflow": opendream.CANVAS.get_workflow()}

@app.get("/schema/{op_name}")
async def schema(op_name: str) -> Dict[str, Any]:
    if op_name not in opendream.operators:
        raise HTTPException(status_code=400, detail=f"Operator {op_name} not found")
    
    params = []
    
    for name, param in inspect.signature(opendream.operators[op_name]).parameters.items():
        if name == "kwargs" or name == "args":
            continue
        params.append({
            "name": name,
            "default": param.default if param.default is not inspect.Parameter.empty else None,
            "type": param.annotation.__name__ if param.annotation is not inspect.Parameter.empty else None
        })
    
    params_dict = {
        "params" : params
    }
    
    return params_dict

@app.get("/state")
async def state() -> Dict[str, Any]:
    return {"layers": opendream.CANVAS.get_serialized_layers(), "workflow": opendream.CANVAS.get_workflow()}

# get request because that's easier
@app.get("/delete_layer/{layer_id}")
async def delete_layer(layer_id) -> Dict[str, Any]:
    # returns modified state
    # loop through layers, find layer with id, delete it
    print("layers before delete", opendream.CANVAS.get_serialized_layers())
    opendream.CANVAS.delete_layer(layer_id)
    print("layers after delete", opendream.CANVAS.get_serialized_layers())
    return {"layers": opendream.CANVAS.get_serialized_layers(), "workflow": opendream.CANVAS.get_workflow()}

@app.post("/load_workflow")
async def load_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    # returns modified state
    opendream.CANVAS.load_workflow(payload)
    return {"layers": opendream.CANVAS.get_serialized_layers(), "workflow": opendream.CANVAS.get_workflow()}

@app.post("/save_extension")
async def save_extension(payload: Dict[str, Any]) -> Dict[str, Any]:
    link = payload["link"]
    
    # download extension to extensions folder
    r = requests.get(link, allow_redirects=True)
    open(f"opendream/extensions/{link.split('/')[-1]}", 'wb').write(r.content)

    # reload extensions
    extension_loader.gather_extensions("opendream/extensions/")
    
    return {"success" : True}

# run uvicorn opendream.server:app --reload