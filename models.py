from uagents import Model
from typing import Optional, Dict, Any

class VerifiableDataRequest(Model):
    """
    Request model for fetching verifiable data.
    Example: "Fetch education credential for user_X"
    data_type: The type of data to fetch (e.g., "education_credential", "reputation_score").
    identifier: The unique identifier for the data (e.g., "user_X", "project_Y").
    query_details: Optional additional parameters or specific questions about the data.
    """
    session_id: str
    data_type: str
    identifier: str
    query_details: Optional[str] = None

class VerifiableDataResponse(Model):
    """
    Response model for verifiable data.
    request_data_type: The data type that was requested.
    request_identifier: The identifier that was requested.
    source_description: A description of the data source.
    data_payload: The actual data fetched, as a dictionary.
    verification_summary: A summary of how the data was (notionally) verified.
    timestamp: The timestamp of when the data was fetched/generated.
    error_message: An optional error message if the request failed.
    """
    session_id: str
    request_data_type: str
    request_identifier: str
    source_description: Optional[str] = None
    timestamp: Optional[str] = None
    data_payload: Optional[Dict[str, Any]] = None
    verification_summary: Optional[str] = None
    error_message: Optional[str] = None

class ErrorMessage(Model):
    """
    Standard error message model for simpler error reporting.
    """
    session_id: str
    error: str 