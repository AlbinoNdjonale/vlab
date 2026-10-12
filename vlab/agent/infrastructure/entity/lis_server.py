from .base import BaseModel
from vlab.agent.infrastructure.api import Api

class LisServer(BaseModel):
    __filename__ = 'lis_server'

    __fields__ = ['base_url', 'exam_results']

    base_url: str = ''
    exam_results: list[dict] = []

    def exam_orders(self, data: dict) -> tuple[bool, dict|None]:
        sample_id = data['user_params'][0]
        
        response = Api.get(f'{self.base_url}/exam_orders/{sample_id}')

        if response is None:
            return True, None

        status_code = response['status_code']

        return (
            str(status_code)[0] == '5',
            None if status_code == 404 else response['data']
        )

    def send_results(self, results: list[dict]):
        self.exam_results = results

        ja_tem_um_lis = False

        if ja_tem_um_lis:
            response = Api.post(f'{self.base_url}/send_exam_results', results)
