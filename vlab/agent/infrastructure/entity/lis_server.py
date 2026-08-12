from .base import BaseModel
from vlab.agent.infrastructure.api import Api

class LisServer(BaseModel):
    __filename__ = 'list_server'

    __fields__ = ['base_url']

    base_url: str = ''

    def exam_orders(self, data: dict) -> tuple[bool, dict|None]:
        sample_id = data['user_params'][0]
        
        response = Api.get(f'{self.base_url}/tests/{sample_id}')

        if response is None:
            return True, None

        status_code = response['status_code']

        return (
            str(status_code)[0] == '5',
            None if status_code == 404 else response['data']
        )
