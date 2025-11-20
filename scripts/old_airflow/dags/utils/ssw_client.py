"""
SSW System Client

Handles HTTP requests to SSW tracking system.
Fetches tracking HTML for Brazilian shipments.
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Constants
SSW_URL = "https://ssw.inf.br/2/resultSSW_dest_nro"
REQUEST_TIMEOUT = 30.0
MIN_VALID_HTML_LENGTH = 100


class SSWClient:
    """Client for SSW tracking system"""

    @staticmethod
    def get_tracking_html(cpf_cnpj: str, nota_fiscal: str) -> Optional[str]:
        """
        Fetch tracking HTML from SSW system

        Args:
            cpf_cnpj: CPF or CNPJ number (with or without formatting)
            nota_fiscal: Invoice number (with or without formatting)

        Returns:
            HTML content string or None if request fails
        """
        clean_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
        clean_nf = ''.join(filter(str.isdigit, nota_fiscal))

        logger.info(f"Fetching SSW tracking for CNPJ: {clean_cnpj}, NF: {clean_nf}")

        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.post(
                    SSW_URL,
                    data={
                        "cnpjdest": clean_cnpj,
                        "NR": clean_nf
                    }
                )

                if response.status_code != 200:
                    logger.warning(
                        f"SSW request failed with status {response.status_code} "
                        f"for CNPJ: {clean_cnpj}, NF: {clean_nf}"
                    )
                    return None

                # Decode with ISO-8859-1 (Brazilian Portuguese encoding)
                html_content = response.content.decode("ISO-8859-1")

                if len(html_content) < MIN_VALID_HTML_LENGTH:
                    logger.warning(f"SSW response too short for CNPJ: {clean_cnpj}, NF: {clean_nf}")
                    return None

                logger.info(f"Successfully fetched tracking data from SSW")
                return html_content

        except httpx.TimeoutException:
            logger.error(f"Timeout fetching SSW data for CNPJ: {cpf_cnpj}, NF: {nota_fiscal}")
            return None
        except Exception as e:
            logger.error(f"Error fetching SSW data: {e}", exc_info=True)
            return None
