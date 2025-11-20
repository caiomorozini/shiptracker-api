from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
import json
import re
import os
import urllib3
from dotenv import load_dotenv
import os
import logging
from typing import Dict, Any, Optional, List
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

load_dotenv()

class ShipTrackerAPIClient:
    """Client for interacting with ShipTracker API"""

    def __init__(self):
        self.base_url = os.getenv('SHIPTRACKER_API_URL', 'http://localhost:8000')
        self.email = os.getenv('SHIPTRACKER_API_EMAIL')
        self.password = os.getenv('SHIPTRACKER_API_PASSWORD')
        self.token = None
        self.token_expires_at = None

    def _ensure_authenticated(self):
        """Ensure we have a valid token"""
        if not self.token:
            self._authenticate()

    def _authenticate(self):
        """Authenticate and get access token"""
        url = f"{self.base_url}/api/auth/login"
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    url,
                    data={
                        "username": self.email,
                        "password": self.password
                    }
                )
                response.raise_for_status()
                data = response.json()
                self.token = data["access_token"]
                logger.info("Successfully authenticated with API")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        self._ensure_authenticated()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    # ==================== Shipments ====================

    def get_active_shipments(self) -> List[Dict[str, Any]]:
        """Get all active shipments that need tracking"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/shipments",
                    headers=self._get_headers(),
                    params={
                        "status": "in_transit,pending",
                        "limit": 1000
                    }
                )
                response.raise_for_status()
                data = response.json()
                shipments = data.get('items', [])
                logger.info(f"Found {len(shipments)} active shipments")
                return shipments

        except Exception as e:
            logger.error(f"Failed to get active shipments: {e}")
            raise

    def get_shipment_by_id(self, shipment_id: str) -> Optional[Dict[str, Any]]:
        """Get shipment details by ID"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/shipments/{shipment_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Shipment {shipment_id} not found")
                return None
            raise

    def update_shipment(self, shipment_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update shipment information"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.patch(
                    f"{self.base_url}/api/shipments/{shipment_id}",
                    headers=self._get_headers(),
                    json=data
                )
                response.raise_for_status()
                logger.info(f"Updated shipment {shipment_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Failed to update shipment {shipment_id}: {e}")
            raise

    def create_tracking_event(
        self,
        shipment_id: str,
        status: str,
        description: str,
        location: Optional[str] = None,
        occurred_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a tracking event for a shipment"""
        try:
            event_data = {
                "shipment_id": shipment_id,
                "status": status,
                "description": description,
            }

            if location:
                event_data["location"] = location

            if occurred_at:
                event_data["occurred_at"] = occurred_at.isoformat()

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/api/shipments/{shipment_id}/events",
                    headers=self._get_headers(),
                    json=event_data
                )
                response.raise_for_status()
                logger.info(f"Created tracking event for shipment {shipment_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Failed to create tracking event: {e}")
            raise

    def get_shipment_events(self, shipment_id: str) -> List[Dict[str, Any]]:
        """Get all tracking events for a shipment"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/shipments/{shipment_id}/events",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to get shipment events: {e}")
            raise

    # ==================== Clients ====================

    def get_client_by_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get client details by ID"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url}/api/clients/{client_id}",
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Client {client_id} not found")
                return None
            raise

    # ==================== Notifications ====================

    def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        related_shipment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a notification in the system"""
        try:
            notification_data = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "type": notification_type
            }

            if related_shipment_id:
                notification_data["related_shipment_id"] = related_shipment_id

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/api/notifications",
                    headers=self._get_headers(),
                    json=notification_data
                )
                response.raise_for_status()
                logger.info(f"Created notification for user {user_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            raise


# Define os argumentos padrão para a DAG
default_args = {
    'owner': 'caiomorozini',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 8),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def get_token_from_shiptracker_api():
    """Função que obtém o token para acessar a API"""

    response =  urllib3.PoolManager().request(
        "POST",
        f"{os.environ['SHIPTRACKER_API_URL']}/api/auth/login",
        fields={
            'username':os.environ['SHIPTRACKER_API_EMAIL'],
            'password':os.environ['SHIPTRACKER_API_PASSWORD']
        },
        timeout=urllib3.Timeout(connect=5.0, read=5.0),
        retries=urllib3.Retry(connect=2, read=2, redirect=2),
    )

    token_dict_response = json.loads(response.data.decode())
    token_type = token_dict_response['token_type']
    access_token = token_dict_response['access_token']

    return token_type, access_token

def get_cnpjs_from_shiptracker_api(**kwargs) -> dict:
    """Faz a requisição GET para obter todos os cnpjs da base de dados"""

    _, access_token = kwargs["ti"].xcom_pull(task_ids="get_token_from_shiprtacker_api")

    response =  urllib3.PoolManager().request(
        "GET",
        f"{os.environ['SHIPTRACKER_API_URL']}/api/shipments",
        headers={'Authorization': f'Bearer {access_token}'},
         params={
            "status": "in_transit,pending",
            "limit": 1000
        },
        timeout=urllib3.Timeout(connect=5.0, read=5.0),
        retries=urllib3.Retry(connect=2, read=2, redirect=2),
    )

    dados = json.loads(response.data.decode())

    return dados


def get_html_from_SSWapi(**kwargs):
    """Obtém os htmls do ssw para cada nota fiscal e cnpj"""

    dados = kwargs["ti"].xcom_pull(task_ids="get_cnpjs_from_shiptracker_api")

    htmls =[]
    for dado in dados['data']:

        cpfcnpj = int(dado['cnpj']) #"10882594001056"
        nota_fiscal = int(dado['nf'])

        response =  urllib3.PoolManager().request(
            "POST",
            f"https://ssw.inf.br/2/resultSSW_dest_nro",
            fields={"cnpjdest": cpfcnpj, "NR": nota_fiscal},
            timeout=urllib3.Timeout(connect=5.0, read=5.0),
            retries=urllib3.Retry(connect=2, read=2, redirect=2),
        )

        # Check if the request was successful
        if response.status != 200:
            continue

        else:
            logging.info("Request was successful")
            htmls.append(
                {
                    "cnpj": dado['cnpj'],
                    "nf": dado['nf'],
                    "html": response.data.decode("ISO-8859-1"),
                    "email": dado['email'],
                    "id": dado['id'],
                }
            )

    return htmls

def parse_html(**kwargs):
    """"Realiza o parser do html obtendo as informações da encomenda"""

    htmls = kwargs["ti"].xcom_pull(task_ids="get_html_from_ssw")
    dados_extraidos = []

    for html in htmls:
        if not html:
            raise ValueError("No data to parse")

        # Get the table from the HTML
        soup = BeautifulSoup(html.get("html"), 'html5lib')

        ship_status = [y.get_text() for y in soup.find_all("p", class_="tdb")]

        data_from_html = {
            "unidade": re.findall(r"(\d{4})", ship_status[0])[0],
            "local": " ".join(re.findall(r"(\w+)", ship_status[1])[:2]),
            "data": re.findall(r"(\d{2}/\d{2}/\d{2})", ship_status[1])[0],
            "hora": re.findall(r"(\d{2}:\d{2})", ship_status[1])[0],
            "status": ship_status[2].split("  ")[0],
        }

        logging.info(dados_extraidos)
        dados_extraidos.append({
            **html,
            **data_from_html,
        })
    return dados_extraidos


def send_email_with_data(**kwargs):
    """""Envia um email com a atualização da entrega para cada cnpj referente a uma dada nota fiscal"""
    
    # Enviar um email para cada item na lista de dados
    data = kwargs["ti"].xcom_pull(task_ids="parse_html")

    _, access_token = kwargs["ti"].xcom_pull(task_ids="get_token_from_shiprtacker_api")
    pool = urllib3.PoolManager()
    for item in data:
        # Se o status for entregue, finalizar o rastreamento
        if item["status"] == "MERCADORIA ENTREGUE":
            logging.info("Finalizando o rastreamento para o CNPJ %s e NF %s", item['cnpj'], item['nf'])


            response =  pool.request(
                "PUT",
                f"{os.environ['SHIPTRACKER_API_URL']}/api/v1/ship/tracker/end_tracking/{item['id']}",
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=urllib3.Timeout(connect=5.0, read=5.0),
                retries=urllib3.Retry(connect=2, read=2, redirect=2),
            )
            if response.status != 204:
                raise ValueError(f"Request failed with status code {response.status}")

        # Checando última atualização do status, se for a mesma, não enviar email
        logging.info("Checando última atualização para o CNPJ %s e NF %s", item['cnpj'], item['nf'])
        response =  pool.request(
            "GET",
            f"{os.environ['SHIPTRACKER_API_URL']}/api/v1/ship/shipments/get_last_update/{item['id']}",
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=urllib3.Timeout(connect=5.0, read=5.0),
            retries=urllib3.Retry(connect=2, read=2, redirect=2),
        )
        last_update = json.loads(response.data.decode())

        if last_update.get('description') == item['status'].lower() \
        or (last_update.get('data') == item['data'] \
        and last_update.get('hora') == item['hora']):
            logging.info("Não há atualizações para o CNPJ %s e NF %s", item['cnpj'], item['nf'])
            logging.info("Status atual: %s", item['status'].lower())
            logging.info("Última atualização: %s", last_update['description'])
            logging.info("Seguindo para o próximo item...")
            continue

        logging.info("Nova atualização para o CNPJ %s e NF %s encontrada!", item['cnpj'], item['nf'])
        logging.info("Cadastro atualizado com sucesso! Novo status: %s", item['status'])
        logging.info("Enviando email para os emails cadastrados...")
        logging.debug("Emails: %s", item['email'])
        subject = f"Status da entrega pedido {item['nf']} - {item['status']}"

        # Abrindo logo para inserir diretamente no html
        html_content = f"""
        <html>
            <head>
                <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    padding: 10px;
                    background-color: #ffcc00;
                    border-radius: 10px 10px 0 0;
                }}
                .header img {{
                    width: 50px;
                    height: 50px;
                }}
                .header h1 {{
                    margin: 10px 0;
                    font-size: 24px;
                    color: #333333;
                }}
                .content {{
                    padding: 20px;
                    text-align: center;
                }}
                .content h2 {{
                    font-size: 20px;
                    color: #333333;
                }}
                .content p {{
                    font-size: 16px;
                    color: #666666;
                    margin: 5px 0;
                }}
                .button {{
                    margin: 20px 0;
                    padding: 10px 20px;
                    background-color: #ffcc00;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                }}
                .details {{
                    margin: 20px 0;
                    padding: 20px;
                    background-color: #ffcc00;
                    color: #333333;
                    border-radius: 10px;
                }}
                .details p {{
                    margin: 10px 0;
                }}
                .details .label {{
                    font-weight: bold;
                }}
                .footer {{
                    background-color: #ffcc00;
                    color: #ffffff;
                    padding: 10px;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                }}
                </style>
            </head>
            <body>
                <div class="container">
                <div class="header">
                    <h1>Seu pedido nº{item["nf"]} foi atualizado! 🚚</h1>
                </div>
                <div class="content">
                    <div class="details">
                    <h2>Detalhes da entrega</h2>
                    <p><span class="label">CNPJ:</span> {item["cnpj"]}</p>
                    <p><span class="label">Nota fiscal:</span> {item["nf"]}</p>
                    <p><span class="label">Status:</span> {item["status"]}</p>
                    <p><span class="label">Localização:</span> {item["local"]}</p>
                    <p><span class="label">Data:</span> {item["data"]}:{item["hora"]}</p>
                    </div>
                    <a
                    href="https://ssw.inf.br/2/rastreamento_dest?pwd=2&"
                    class="button"
                    style="
                        background-color: #ffcc00;
                        color: black;
                        font-size: 16px;
                        text-decoration: none;
                        border-radius: 5px;
                        display: inline-block;
                    "
                    >Acompanhe aqui</a
                    >
                </div>

                <!-- O foter tem que ficar um pouco posicionado para cima -->
                <div class="footer" style="font-color: black; color: #333333;">
                    <p>Obrigado por comprar conosco! 🛒</p>

                </div>

                <img
                style="display: block; margin: 0 auto;"
                src="cid:logo_vector.ico"
                alt="logo"
                />
                </div>
            </body>
            </html>
            """


        # Enviar o email
        email_op = EmailOperator(
            task_id=f"send_email_{item['cnpj']}_{item['nf']}",
            to=item["email"],
            subject=subject,
            html_content=html_content,
            dag=dag,
            files=["logo_vector.ico"],
        )
        email_op.execute(kwargs)  # É errado, mas funcionou por agora

        logging.info("Atualizando na base de dados...")

        response =  pool.request(
            "POST",
            f"{os.environ['SHIPTRACKER_API_URL']}/api/v1/ship/shipments/",
            headers={'Authorization': f'Bearer {access_token}'},
            body=json.dumps({
                "unidade": item["unidade"].lower(),
                "local": item["local"].lower(),
                "data": item["data"],
                "hora": item["hora"],
                "status": item["status"].lower(),
                "cnpj_id": item["id"]
            }),
            timeout=urllib3.Timeout(connect=5.0, read=5.0),
            retries=urllib3.Retry(connect=2, read=2, redirect=2),
        )
        if response.status != 200:
            raise ValueError(f"Request failed with status code {response.status}")



with DAG(
    "ssw_workflow",
    default_args=default_args,
    description="Um exemplo simples de uma DAG",
    schedule="@once",#"0/1 * * ? * * *",
    catchup=False
) as dag:

    start = EmptyOperator(
        task_id="start",
        dag=dag,
    )


    get_token_from_api = PythonOperator(
        task_id='get_token_from_shiprtacker_api',
        python_callable= get_token_from_shiptracker_api,
        dag=dag
    )

    get_cnpjs_from_api = PythonOperator(
        task_id="get_cnpjs_from_shiptracker_api",
        python_callable=get_cnpjs_from_shiptracker_api,
        dag=dag
    )

    get_html_from_ssw = PythonOperator(
        task_id="get_html_from_ssw",
        python_callable=get_html_from_SSWapi,
        dag=dag,
    )
    
    parser_html = PythonOperator(
        task_id="parse_html",
        python_callable=parse_html,
        dag=dag,
    )

    send_email = PythonOperator(
        task_id="send_email",
        python_callable=send_email_with_data,
        dag=dag,
    )

    end = EmptyOperator(
        task_id="end",
        dag=dag
    )

    start >> get_token_from_api >> get_cnpjs_from_api >> get_html_from_ssw >> parser_html >> send_email >> end

if __name__ == "__main__":
    dag.test()