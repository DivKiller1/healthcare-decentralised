# backend/shared/utils.py
import os
import httpx
import uuid
import logging
from typing import Optional

# GCP Native Integration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if GCP_PROJECT_ID:
    try:
        import google.cloud.logging
        from google.cloud import error_reporting
        
        # Setup Cloud Logging
        log_client = google.cloud.logging.Client(project=GCP_PROJECT_ID)
        log_client.setup_logging()
        
        # Setup Error Reporting
        error_client = error_reporting.Client(project=GCP_PROJECT_ID)
    except ImportError:
        pass

logger = logging.getLogger("healthcare-saas")
logger.setLevel(logging.INFO)

AUDIT_SERVICE_URL = os.getenv("AUDIT_SERVICE_URL", "http://audit-svc")

async def log_event(actor_id: uuid.UUID, action_type: str, entity_type: str, entity_id: uuid.UUID, metadata: Optional[dict] = None):
    payload = {
        "actor_id": str(actor_id),
        "action_type": action_type,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "metadata": metadata
    }
    
    # GCP Operations Suite Capture
    log_msg = f"AUDIT_EVENT: {action_type} | Actor: {actor_id} | Entity: {entity_type}/{entity_id}"
    logger.info(log_msg)
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{AUDIT_SERVICE_URL}/internal/log", json=payload, timeout=2.0)
    except Exception as e:
        logger.error(f"AUDIT_SERVICE_UNREACHABLE: {e}")
        # Report error to GCP Error Reporting if available
        if 'error_client' in globals():
            error_client.report_exception()

async def report_exception():
    if 'error_client' in globals():
        error_client.report_exception()
