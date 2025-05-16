import os
import asyncio
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

from uagents import Agent, Context, Model, Bureau, Protocol
from uagents.setup import fund_agent_if_low
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage as UAgentsErrorMessage

from models import VerifiableDataRequest, VerifiableDataResponse, ErrorMessage
from data_source_handler import fetch_verifiable_data
from chat_protocol_integration import (
    verifiable_data_chat_proto,
    create_chat_message,
    format_response_for_chat,
    get_structured_output_from_gemini
)

AGENT_MAILBOX_KEY = os.environ.get("VERIFIABLE_DATA_AGENT_MAILBOX_KEY", "default_verifiable_data_agent_mailbox")
AGENT_PORT = int(os.environ.get("VERIFIABLE_DATA_AGENT_PORT", 8001))

# Agent setup
agent = Agent(
    name="VerifiableDataAgent",
    port=AGENT_PORT,
    seed=os.environ.get("VERIFIABLE_DATA_AGENT_SEED", "verifiable_data_agent_secret_seed"),
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

fund_agent_if_low(agent.wallet.address())

# --- Quota Protocol ---
default_hourly_rate_limit = RateLimit(window_size_minutes=60, max_requests=100)
quota_proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="VerifiableDataQuotaProtocol",
    version="0.1.0",
    default_rate_limit=default_hourly_rate_limit,
)
agent.include(quota_proto, publish_manifest=True)

# --- Health Check Protocol ---
class HealthCheckRequest(Model):
    pass

class AgentHealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

class AgentHealthResponse(Model):
    agent_name: str
    status: AgentHealthStatus
    message: str = ""

health_protocol = Protocol(name="VerifiableDataHealthProtocol", version="0.1.0")

async def check_agent_health(ctx: Context) -> tuple[AgentHealthStatus, str]:
    try:
        health_check_result_dict = await fetch_verifiable_data(            
            data_type="crypto_price", 
            identifier="bitcoin",
            query_details="vs_currency=usd"
        )
        if not health_check_result_dict.get("error_message"):
            return AgentHealthStatus.HEALTHY, "CoinGecko API connection successful."
        else:
            error = health_check_result_dict.get("error_message", "Unknown error during health check data fetch.")
            ctx.logger.warning(f"Health check: Data fetch failed or returned error: {error}")
            return AgentHealthStatus.UNHEALTHY, f"Failed to fetch test data from CoinGecko: {error}"
    except Exception as e:
        ctx.logger.error(f"Health check exception: {e}")
        return AgentHealthStatus.UNHEALTHY, f"Exception during health check: {str(e)}"

@health_protocol.on_message(HealthCheckRequest, replies={AgentHealthResponse})
async def handle_health_check(ctx: Context, sender: str, _msg: HealthCheckRequest):
    status, message = await check_agent_health(ctx)
    await ctx.send(sender, AgentHealthResponse(agent_name=agent.name, status=status, message=message))

agent.include(health_protocol, publish_manifest=True)

# --- Include Chat Protocol ---
agent.include(verifiable_data_chat_proto, publish_manifest=True)

# The structured_output_protocol and its handler are removed as Gemini calls are now direct.

# --- Main Request Handler (for structured VerifiableDataRequest) ---
@agent.on_message(VerifiableDataRequest, replies=None)
async def handle_verifiable_data_request(ctx: Context, sender: str, request: VerifiableDataRequest):
    ctx.logger.info(f"Received VerifiableDataRequest from {sender} for session {request.session_id}: {request}")
    
    if not hasattr(request, 'session_id') or not request.session_id:
        ctx.logger.error(f"Critical: VerifiableDataRequest is missing session_id. Cannot process: {request}")
        return

    data_dict = await fetch_verifiable_data(
        data_type=request.data_type,
        identifier=request.identifier,
        query_details=request.query_details
    )

    response_model: Model
    if data_dict.get("error_message"):
        ctx.logger.warning(f"Data fetching returned an error for session {request.session_id}: {data_dict.get('error_message')}")
        response_model = ErrorMessage(
            session_id=request.session_id, 
            error=data_dict["error_message"]
        )
    else:
        response_model = VerifiableDataResponse(
            session_id=request.session_id,
            request_data_type=data_dict.get("request_data_type", request.data_type),
            request_identifier=data_dict.get("request_identifier", request.identifier),
            source_description=data_dict.get("source_description"),
            timestamp=data_dict.get("timestamp"),
            data_payload=data_dict.get("data_payload"),
            verification_summary=data_dict.get("verification_summary")
        )
        ctx.logger.info(f"Successfully fetched data for session {request.session_id}, preparing response model.")

    await ctx.send(ctx.agent.address, response_model)

@agent.on_message(VerifiableDataResponse, replies=None)
@agent.on_message(ErrorMessage, replies=None)
async def handle_internal_response(ctx: Context, sender: str, response: any):
    if not hasattr(response, 'session_id') or not response.session_id:
        ctx.logger.error(f"Critical: Response model is missing session_id. Cannot route response: {response}")
        return

    original_user_address = ctx.storage.get(str(response.session_id))

    if not original_user_address:
        ctx.logger.error(f"Could not find original user address for session_id: {response.session_id} to send final response. This is a critical flow error.")
        return

    if isinstance(response, VerifiableDataResponse):
        ctx.logger.info(f"Forwarding VerifiableDataResponse to user for session {response.session_id}: ID {response.request_identifier}")
        formatted_text_response = format_response_for_chat(response)
    elif isinstance(response, ErrorMessage):
        ctx.logger.info(f"Forwarding ErrorMessage to user for session {response.session_id}: {response.error}")
        error_response_for_formatting = VerifiableDataResponse(
            session_id=response.session_id, 
            request_data_type="error_report", 
            request_identifier="unknown_request_due_to_error", 
            error_message=response.error
        )
        formatted_text_response = format_response_for_chat(error_response_for_formatting)
    else:
        ctx.logger.error(f"Received unknown response type for session {response.session_id}: {type(response)}. Sending generic error to user.")
        generic_error_response = VerifiableDataResponse(
            session_id=response.session_id, 
            request_data_type="system_error", 
            request_identifier="unknown",
            error_message="An unexpected internal error occurred while processing your request."
        )
        formatted_text_response = format_response_for_chat(generic_error_response)

    final_chat_message = create_chat_message(text=formatted_text_response, end_session=True)
    await ctx.send(original_user_address, final_chat_message)
    ctx.logger.info(f"Sent final formatted response to original user: {original_user_address} for session {response.session_id}")

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Starting VerifiableDataAgent '{agent.name}' with address: {agent.address}")
    ctx.logger.info(f"Agent Web UI: http://127.0.0.1:{AGENT_PORT}/submit")
    
    # Use the globally defined AGENT_MAILBOX_KEY to construct the mailbox identifier
    expected_mailbox_identifier = f"{AGENT_MAILBOX_KEY}@https://agentverse.ai"
    ctx.logger.info(f"Agent Mailbox configured for: {expected_mailbox_identifier}")
    
    # Construct inspector URL using the agent's on-chain address and known Agentverse host
    # This assumes the standard Agentverse host is being used for the mailbox.
    inspector_url = f"https://agentverse.ai/inspect/?address={agent.address}"
    ctx.logger.info(f"Agent inspector (via Agentverse): {inspector_url}")

if __name__ == "__main__":
    print(f"Starting VerifiableDataAgent '{agent.name}' with address: {agent.address}")
    
    # Display mailbox info using the globally defined AGENT_MAILBOX_KEY
    expected_mailbox_identifier_main = f"{AGENT_MAILBOX_KEY}@https://agentverse.ai"
    print(f"Mailbox: {expected_mailbox_identifier_main}")
    
    agent.run() 