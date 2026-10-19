from .base import BaseModel
from vlab.agent.infrastructure.api import Api

class LisServer(BaseModel):
    __filename__ = 'lis_server'

    __fields__ = ['exam_results', 'lote_exam_orders']

    base_url: str = ''
    exam_results: list[dict] = []
    lote_exam_orders: list[dict] = []

    def exam_orders(self, data: dict) -> tuple[bool, dict|None]:
        sample_id = data['user_params'][0]

        for exam_order in self.lote_exam_orders:
            if exam_order["id"] == sample_id:
                return False, {
                    "patient": exam_order["patient"],
                    "exam_orders": exam_order["exams"]
                }
        
        response = Api.get(f'{self.base_url}/exam_orders/{sample_id}')

        if response is None:
            return True, None

        status_code = response['status_code']

        return (
            str(status_code)[0] == '5',
            None if status_code == 404 else response['data']
        )

    def insert_lote_exam_orders(self, exam_orders: list[dict]):
        self.lote_exam_orders.extend(exam_orders)

    def send_results(self, results: list[dict]):
        self.exam_results = results

        response = Api.post(f'{self.base_url}/send_exam_results', results)

    def set_base_url(self, base_url: str):
        self.base_url = base_url
