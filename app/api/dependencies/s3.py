"""
Módulo para gerenciamento de arquivos no S3 (MinIO).
"""
import boto3
from app.core.config import get_app_settings

settings = get_app_settings()

def get_s3_resource():
    """
    Retorna o recurso S3 (MinIO) configurado.
    """
    return boto3.resource(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        aws_session_token=None,
        config=boto3.session.Config(signature_version="s3v4"),
    )
