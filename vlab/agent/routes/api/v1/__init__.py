from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from serial.tools import list_ports

from vlab.agent.gateway import Gateway

v1_routes = APIRouter()

@v1_routes.get('/serialports')
def serial_ports():
    return [
        {
            'id': port.name,
            'name': port.product,
            'description': port.description,
            'display': ':'.join([
                id for id in [port.product, port.description, port.name]
                if id and not id == 'n/a'
            ])
        }
        for port in list_ports.comports()
        if port.vid or port.pid
    ]

@v1_routes.get('/devices')
def devices(request: Request):
    gateway: Gateway = request.app.state.gateway

    return [
        {key: value for key, value in device.items() if key not in ['id', 'conn']}
        for device in gateway.get_devices
    ]

@v1_routes.post('/config_device', status_code = 201)
async def config_device(request: Request):
    try:
        data = await request.json()
    except:
        return JSONResponse({"detail": "Invalid body"}, 400)

    if (addres := data.get("device_address")) is None or addres.split() == '':
        return JSONResponse({"'device_address' is required"}, 400)

    gateway: Gateway = request.app.state.gateway
    
    if data.get('contract'):
        try:
            gateway.apparatus_config.create_config(data['device_address'], data['contract'])
        except:
            return JSONResponse({"detail": "Error to save config, Try Again"}, 500)

    return {"detail": "Config saved"}
