from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from serial.tools import list_ports

from vlab.agent.gateway import Gateway

v1_routes = APIRouter()

@v1_routes.get('/serial_ports')
def serial_ports():
    return [
        {
            'id': port.device,
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

@v1_routes.post('/connect_device')
async def connect_device(request: Request):
    try:
        connection = await request.json()
    except:
        return JSONResponse({"detail": "Invalid body"}, 400)

    if connection.get('address') is None:
        return JSONResponse({'detail': f"Property 'address' is required"}, 400)

    gateway: Gateway = request.app.state.gateway

    gateway.add_device(connection.get('address'), connection.get('port'))

    return {'detail': 'Proccess add'}

@v1_routes.get('/device/{address}')
async def get_device(request: Request, address: str):
    gateway: Gateway = request.app.state.gateway

    client = gateway.get_client(address, by = 'address')

    if client is None:
        return JSONResponse({'detail': 'Device not found'}, 404)
     
    return {key: value for key, value in client.items() if key not in ['id', 'conn']}

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

    if (address := data.get("device_address")) is None or address.split() == '':
        return JSONResponse({"'device_address' is required"}, 400)

    gateway: Gateway = request.app.state.gateway

    if data.get('protocol'):
        try:
            gateway.apparatus_config.set_protocol(data['protocol'], address)
        except:
            return JSONResponse({"detail": "Error to save config, Try Again"}, 500)
    
    if data.get('contract'):
        try:
            gateway.apparatus_config.set_contract(data['device_address'], data['contract'])
        except:
            return JSONResponse({"detail": "Error to save config, Try Again"}, 500)

    return {"detail": "Config saved"}

@v1_routes.delete('/delete_contract/{address}')
def delete_contract(request: Request, address: str):
    gateway: Gateway = request.app.state.gateway

    client = gateway.get_client(address, by = 'address')

    if client is None:
        return JSONResponse({'detail': 'Device not found'}, 404)
    
    gateway.apparatus_config.remove_contract(client.get('name', ''), client['address'])
    
    return {'detail': 'Contract deleted'}

@v1_routes.get('/exam_results')
def get_exam_results(request: Request):
    gateway: Gateway = request.app.state.gateway

    return gateway.lis_server.exam_results

@v1_routes.get('/exam_results/{sample_id}')
def get_exam_result(request: Request, sample_id: str):
    gateway: Gateway = request.app.state.gateway

    for exam_result in gateway.lis_server.exam_results:
        if exam_result['sample_id'] == sample_id:
            return exam_result

    return JSONResponse({'detail': 'Exam Result not found'}, 404)
