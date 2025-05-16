from datetime import datetime, timezone
from uuid import uuid4
from typing import Any, Union, Dict
import json
import os
import asyncio
from dotenv import load_dotenv
import re

load_dotenv()

from uagents import Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
# Reverting to google.generativeai as it's more common and stable for this use case
import google.generativeai as genai
# from google.genai import types as genai_types # Not using this low-level client for now

from models import VerifiableDataRequest, VerifiableDataResponse

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest") 

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable is not set. Gemini LLM calls will fail.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY) # Configure once globally
        print("Gemini API configured successfully.") # Added for confirmation
    except Exception as e:
        print(f"Error configuring Gemini API with key: {e}. Ensure key is valid.")

# Main chat protocol for Verifiable Data Agent
verifiable_data_chat_proto = Protocol(name="VerifiableDataChatProtocol", version="1.2", spec=chat_protocol_spec) # Incremented version

def create_chat_message(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )

def normalize_identifier(identifier: str, data_type: str) -> str:
    """
    Normalize identifiers to match the format used in the database.
    Converts full names to lowercase with underscores and removes spaces.
    """
    if not identifier:
        return identifier
        
    # Handle special cases for education credentials
    if data_type == "education_credential":
        # Convert names like "Alex Chen" to "alex_chen"
        return identifier.lower().replace(" ", "_")
    
    # Handle special cases for reputation scores
    if data_type == "reputation_score":
        # Import the reputation normalizer
        from reputation_score import normalize_reputation_identifier
        return normalize_reputation_identifier(identifier)
    
    # Handle other data types if needed
    return identifier

async def get_structured_output_from_gemini(ctx: Context, user_query: str, target_schema: dict) -> Union[Dict[str, Any], None]:
    if not GEMINI_API_KEY:
        ctx.logger.error("GEMINI_API_KEY not found in environment variables.")
        return None

    schema_json_string = json.dumps(target_schema)
    prompt = f"""
    You are an AI assistant for the Fetch.ai Verifiable Data Agent. Your task is to understand a user's request for verifiable data and extract specific pieces of information into a structured JSON format.
    The required JSON output schema is strictly: {schema_json_string}

    User request: "{user_query}"

    Guidelines for populating the schema:
    - 'data_type': Infer from the request. Available data types include:
        * 'crypto_price' - For cryptocurrency price queries
        * 'education_credential' - For educational achievements, degrees, certifications  
        * 'supply_chain_status' - For product origins, tracking, sustainability
        * 'carbon_footprint' - For emissions/environmental impact of products, companies, or activities
        * 'reputation_score' - For developer/service/DAO reputation and trust metrics
    
    - 'identifier': The main subject of the query. Examples by data type:
        * For 'crypto_price': cryptocurrency name (e.g., "bitcoin", "ethereum", "fetch-ai")
        * For 'education_credential': person name or ID (e.g., "john_smith", "jane_doe", "alex_chen") 
          Note that full names like "Alex Chen" will be converted to lowercase with underscores ("alex_chen")
        * For 'supply_chain_status': product name (e.g., "costa_rica_coffee", "ecophone_x1")  
        * For 'carbon_footprint': product, company, or activity (e.g., "macbook_pro", "greencorp", "london_nyc_flight", "california_electricity")
        * For 'reputation_score': entity name (e.g., "alex_developer", "decentra_dao", "trustdata_service")
    
    - 'query_details': Optional parameters based on data type:
        * For 'crypto_price': target currency (e.g., "vs_currency=eur"). Default is "vs_currency=usd"
        * For 'carbon_footprint': scope type (e.g., "scope=company", "scope=activity"). Default is product scope
        * For 'reputation_score': specific aspect (e.g., "aspect=developer", "aspect=contributor", "aspect=service")
    
    Only output the raw JSON object that strictly conforms to the schema. Do not include any other text, explanations, or markdown formatting (like ```json ```) around the JSON. Your response must be solely the JSON object.
    """

    def call_gemini_sync():
        try:
            # Define generation config for JSON output
            generation_config = genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
            model = genai.GenerativeModel(
                GEMINI_MODEL_NAME, 
                generation_config=generation_config
            )
            response = model.generate_content(contents=[prompt])
            return response.text
        except Exception as e:
            print(f"[Gemini Sync Call Error in chat_protocol_integration] Error calling Gemini API: {e}") 
            return None

    try:
        json_string = await asyncio.to_thread(call_gemini_sync)
        if not json_string:
            ctx.logger.error("Gemini returned an empty or error response in chat_protocol.")
            return None
        
        cleaned_json_string = json_string.strip()
        # Minimal cleanup for potential markdown, though application/json should prevent it
        if cleaned_json_string.startswith("```json"):
            cleaned_json_string = cleaned_json_string[7:-3].strip()
        elif cleaned_json_string.startswith("```"):
             cleaned_json_string = cleaned_json_string[3:-3].strip()

        parsed_json = json.loads(cleaned_json_string)
        return parsed_json
    except json.JSONDecodeError as e:
        ctx.logger.error(f"Failed to decode JSON from Gemini in chat_protocol: {e}. Response: '{json_string}'")
        return None
    except Exception as e:
        ctx.logger.error(f"Generic error during Gemini processing in chat_protocol: {e}")
        return None

@verifiable_data_chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Received ChatMessage from {sender}: {msg.content[0].text if msg.content else 'Empty'}")
    ctx.storage.set(str(ctx.session), sender)
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))

    user_query = None
    for item in msg.content:
        if isinstance(item, TextContent):
            user_query = item.text
            break
        elif isinstance(item, StartSessionContent):
            ctx.logger.info(f"Session started with {sender}")
            continue
    
    if not user_query:
        await ctx.send(sender, create_chat_message("I received an empty message. Please tell me what verifiable data you need."))
        return

    if not GEMINI_API_KEY:
        ctx.logger.error("GEMINI_API_KEY is not set. Cannot process query via Gemini.")
        await ctx.send(sender, create_chat_message("Sorry, I'm not configured correctly to use the LLM for understanding your request right now."))
        return

    structured_data_from_gemini = await get_structured_output_from_gemini(ctx, user_query, VerifiableDataRequest.schema())

    if structured_data_from_gemini:
        try:
            structured_data_from_gemini['session_id'] = str(ctx.session)
            
            data_request = VerifiableDataRequest.parse_obj(structured_data_from_gemini)
            ctx.logger.info(f"Successfully parsed Gemini output into VerifiableDataRequest (session: {ctx.session}): {data_request}")
            await ctx.send(ctx.agent.address, data_request) # Send to self's address
        except Exception as e:
            ctx.logger.error(f"Error parsing Gemini output ({structured_data_from_gemini}) into VerifiableDataRequest (session: {ctx.session}): {e}")
            await ctx.send(sender, create_chat_message(f"Sorry, I had trouble structuring your request after the LLM processed it. Details: {e}"))
    else:
        ctx.logger.error(f"Failed to get structured output from Gemini for query (session: {ctx.session}): {user_query}")
        await ctx.send(sender, create_chat_message("Sorry, I couldn't understand or structure your request using the LLM. Please try rephrasing."))

@verifiable_data_chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received ChatAcknowledgement from {sender} for msg_id: {msg.acknowledged_msg_id}")

def format_response_for_chat(response_data: VerifiableDataResponse) -> str:
    if response_data.error_message:
        return (
            f"# Error Report\n"
            f"**Message:** {response_data.error_message}\n\n"
            f"_Please try again or rephrase your request._"
        )

    # Timestamp formatting
    formatted_timestamp = "N/A"
    try:
        ts_str = str(response_data.timestamp)
        if 'Z' in ts_str:
            dt_object = datetime.fromisoformat(ts_str.replace('Z', '+00:00')).astimezone(timezone.utc)
        else:
            dt_object = datetime.fromisoformat(ts_str).astimezone(timezone.utc)
        formatted_timestamp = dt_object.strftime("%B %d, %Y, %I:%M %p UTC")
    except Exception as e:
        print(f"Error formatting timestamp '{response_data.timestamp}': {e}")
        formatted_timestamp = str(response_data.timestamp) 

    output_lines = [
        f"# Verifiable Data Report",
        f" " # Adding an empty line for spacing instead of --- or emojis
    ]

    identifier = response_data.request_identifier.capitalize()
    data_type_display = response_data.request_data_type.replace('_', ' ').title()

    if response_data.request_data_type == "crypto_price" and isinstance(response_data.data_payload, dict):
        price = response_data.data_payload.get("price")
        currency = response_data.data_payload.get("currency", "usd").upper()
        asset_name = response_data.data_payload.get("asset_id", identifier).capitalize()

        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
        price_symbol = currency_symbols.get(currency, "")

        formatted_price = "N/A"
        if price is not None:
            try:
                formatted_price = f"{price_symbol}{float(price):,.2f} {currency}"
            except ValueError:
                formatted_price = f"{price_symbol}{price} {currency}"

        output_lines.append(f"**Asset:** {asset_name}")
        output_lines.append(f"**Price:** {formatted_price}")
        output_lines.append(f"**Time:** {formatted_timestamp}")
        output_lines.append(f"**Source:** {response_data.source_description}")
        output_lines.append(f"**Verification:** {response_data.verification_summary}")
    
    elif response_data.request_data_type == "education_credential" and isinstance(response_data.data_payload, dict):
        profile = response_data.data_payload.get("profile", {})
        credentials = response_data.data_payload.get("credentials", [])
        
        output_lines.append(f"**Individual:** {profile.get('name', identifier)}")
        output_lines.append(f"**Decentralized ID:** {profile.get('identifierDid', 'N/A')}")
        output_lines.append(f"**Verification Method:** {response_data.verification_summary}")
        output_lines.append(" ")
        
        if credentials:
            output_lines.append("## Verified Credentials")
            for i, cred in enumerate(credentials, 1):
                output_lines.append(f"### {i}. {cred.get('name', 'Credential')}")
                output_lines.append(f"**Type:** {cred.get('type', 'N/A')}")
                output_lines.append(f"**Issuer:** {cred.get('issuer', 'N/A')}")
                output_lines.append(f"**Issue Date:** {cred.get('issueDate', 'N/A')}")
                output_lines.append(f"**Status:** {cred.get('verificationStatus', 'N/A')}")
                output_lines.append(f"**Proof Method:** {cred.get('proofMethod', 'N/A')}")
                output_lines.append(" ")
        else:
            output_lines.append("**No credentials found for this identifier.**")
    
    elif response_data.request_data_type == "supply_chain_status" and isinstance(response_data.data_payload, dict):
        product = response_data.data_payload.get("product", {})
        chain = response_data.data_payload.get("supplyChain", [])
        certifications = response_data.data_payload.get("certifications", [])
        sustainability = response_data.data_payload.get("sustainability", {})
        verification = response_data.data_payload.get("verificationProof", {})
        
        output_lines.append(f"**Product:** {product.get('name', identifier)}")
        output_lines.append(f"**Manufacturer:** {product.get('manufacturer', 'N/A')}")
        
        if certifications:
            output_lines.append(f"**Certifications:** {', '.join(certifications)}")
        
        if sustainability:
            output_lines.append(f"**Carbon Footprint:** {sustainability.get('carbonFootprint', 'N/A')}")
        
        if verification:
            output_lines.append(f"**Verification Method:** {verification.get('method', 'N/A')}")
            output_lines.append(f"**Blockchain Reference:** {verification.get('blockchainReference', 'N/A')}")
        
        output_lines.append(" ")
        
        if chain:
            output_lines.append("## Supply Chain Journey")
            for stage in chain:
                output_lines.append(f"### {stage.get('stage', 'Unknown Stage')}")
                output_lines.append(f"**Location:** {stage.get('location', 'N/A')}")
                output_lines.append(f"**Date:** {stage.get('timestamp', 'N/A')}")
                output_lines.append(f"**Verification:** {stage.get('verificationMethod', 'N/A')} by {stage.get('verifier', 'N/A')}")
                output_lines.append(" ")
        
        output_lines.append(f"**Summary:** {response_data.verification_summary}")
    
    elif response_data.request_data_type == "carbon_footprint" and isinstance(response_data.data_payload, dict):
        # Extract data from payload based on its structure
        product_info = response_data.data_payload.get("productInfo", {})
        company_info = response_data.data_payload.get("companyInfo", {})
        activity_info = response_data.data_payload.get("activityInfo", {})
        
        carbon_data = response_data.data_payload.get("carbonFootprint", {})
        emissions = response_data.data_payload.get("emissions", {})
        verification = response_data.data_payload.get("verification", {})
        
        # Determine the entity type and display accordingly
        if product_info:
            entity_type = "Product"
            entity_name = product_info.get("name", identifier)
            entity_detail = f"Manufacturer: {product_info.get('manufacturer', 'N/A')}"
        elif company_info:
            entity_type = "Company"
            entity_name = company_info.get("name", identifier)
            entity_detail = f"Industry: {company_info.get('industry', 'N/A')}"
        elif activity_info:
            entity_type = "Activity"
            entity_name = activity_info.get("type", identifier)
            entity_detail = f"Details: {activity_info.get('details', 'N/A')}"
        else:
            entity_type = "Entity"
            entity_name = identifier
            entity_detail = ""
        
        output_lines.append(f"**{entity_type}:** {entity_name}")
        output_lines.append(f"**{entity_detail}**")
        
        # Display carbon footprint or emissions data
        if carbon_data:
            output_lines.append(f"**Carbon Footprint:** {carbon_data.get('total', 'N/A')} {carbon_data.get('unit', 'CO2e')}")
            
            if "breakdown" in carbon_data and carbon_data["breakdown"]:
                output_lines.append(" ")
                output_lines.append("### Footprint Breakdown")
                for category, value in carbon_data["breakdown"].items():
                    output_lines.append(f"**{category.capitalize()}:** {value} {carbon_data.get('unit', 'CO2e')}")
        
        elif emissions:
            output_lines.append(f"**Total Emissions:** {emissions.get('total', 'N/A')} {emissions.get('unit', 'CO2e')}")
            
            if "breakdown" in emissions and emissions["breakdown"]:
                output_lines.append(" ")
                output_lines.append("### Emissions Breakdown")
                for scope, value in emissions["breakdown"].items():
                    output_lines.append(f"**{scope.capitalize()}:** {value} {emissions.get('unit', 'CO2e')}")
            
            if "targets" in response_data.data_payload:
                output_lines.append(f"**Reduction Targets:** {response_data.data_payload.get('targets', 'N/A')}")
        
        # Display verification details
        output_lines.append(" ")
        output_lines.append("### Verification Details")
        if verification:
            output_lines.append(f"**Methodology:** {verification.get('methodology', verification.get('standard', 'N/A'))}")
            output_lines.append(f"**Verifier:** {verification.get('verifier', 'N/A')}")
            output_lines.append(f"**Date:** {verification.get('date', 'N/A')}")
        
        output_lines.append(f"**Summary:** {response_data.verification_summary}")
    
    elif response_data.request_data_type == "reputation_score" and isinstance(response_data.data_payload, dict):
        entity_info = response_data.data_payload.get("entityInfo", {})
        scores = response_data.data_payload.get("reputationScores", {})
        stats = response_data.data_payload.get("statistics", {})
        highlights = response_data.data_payload.get("highlights", [])
        verification = response_data.data_payload.get("verification", {})
        
        output_lines.append(f"**Entity:** {entity_info.get('name', identifier)}")
        output_lines.append(f"**Decentralized ID:** {entity_info.get('decentralizedId', 'N/A')}")
        
        if scores:
            output_lines.append(f"**Overall Score:** {scores.get('overall', 'N/A')}/100")
            
            if "breakdown" in scores and scores["breakdown"]:
                output_lines.append(" ")
                output_lines.append("### Score Breakdown")
                for category, score in scores["breakdown"].items():
                    output_lines.append(f"**{category.replace('_', ' ').capitalize()}:** {score}/100")
        
        if stats:
            output_lines.append(" ")
            output_lines.append("### Key Statistics")
            for stat, value in stats.items():
                if isinstance(value, dict):
                    output_lines.append(f"**{stat.replace('_', ' ').capitalize()}:** ")
                    for sub_stat, sub_value in value.items():
                        output_lines.append(f"- {sub_stat.replace('_', ' ').capitalize()}: {sub_value}")
                else:
                    output_lines.append(f"**{stat.replace('_', ' ').capitalize()}:** {value}")
        
        if highlights and isinstance(highlights, list):
            output_lines.append(" ")
            output_lines.append("### Highlights")
            if all(isinstance(item, dict) for item in highlights):
                # If highlights are dictionaries (like projects or contributions)
                for item in highlights:
                    if "name" in item:
                        output_lines.append(f"- **{item.get('name')}**")
                        for key, value in item.items():
                            if key != "name":
                                output_lines.append(f"  {key.capitalize()}: {value}")
            else:
                # If highlights are simple strings (like skills)
                output_lines.append(f"- {', '.join(highlights)}")
        
        output_lines.append(" ")
        output_lines.append("### Verification")
        output_lines.append(f"**Method:** {verification.get('method', 'N/A')}")
        output_lines.append(f"**Attesters:** {', '.join(verification.get('attesters', ['N/A']))}")
        output_lines.append(f"**Summary:** {response_data.verification_summary}")
        
    else:
        # Generic handler for any other data types or when data_payload is not a dictionary
        output_lines.append(f"**Type:** {data_type_display}")
        output_lines.append(f"**Identifier:** {identifier}")
        output_lines.append(f"**Source:** {response_data.source_description}")
        output_lines.append(f"**Time:** {formatted_timestamp}")
        output_lines.append(" ")
        
        # Try to format data_payload as readable content if possible
        if isinstance(response_data.data_payload, dict):
            for key, value in response_data.data_payload.items():
                if isinstance(value, dict):
                    output_lines.append(f"**{key.replace('_', ' ').capitalize()}:**")
                    for sub_key, sub_value in value.items():
                        output_lines.append(f"- {sub_key.replace('_', ' ').capitalize()}: {sub_value}")
                elif isinstance(value, list):
                    output_lines.append(f"**{key.replace('_', ' ').capitalize()}:** {', '.join(map(str, value))}")
                else:
                    output_lines.append(f"**{key.replace('_', ' ').capitalize()}:** {value}")
        else:
            output_lines.append(f"**Data:** {response_data.data_payload}")
        
        output_lines.append(" ")
        output_lines.append(f"**Verification:** {response_data.verification_summary}")
    
    return "\n".join(output_lines) 

async def process_verifiable_data_request(ctx: Context, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a verifiable data request by:
    1. Normalizing the identifier if needed
    2. Fetching the appropriate data
    3. Returning a formatted response
    """
    data_type = request_data.get("data_type")
    identifier = request_data.get("identifier")
    query_details = request_data.get("query_details", "")
    session_id = request_data.get("session_id")
    
    # Normalize the identifier based on data type
    normalized_identifier = normalize_identifier(identifier, data_type)
    
    # Log the normalization if it changed
    if normalized_identifier != identifier:
        ctx.logger.info(f"Normalized identifier from '{identifier}' to '{normalized_identifier}'")
        identifier = normalized_identifier
    
    # Get current timestamp
    timestamp = datetime.datetime.now().isoformat()
    
    try:
        # Fetch the appropriate data based on data_type
        from data_source_handler import fetch_verifiable_data
        result = await fetch_verifiable_data(data_type, identifier, query_details, timestamp)
        
        # Check for error message in result
        if "error_message" in result:
            ctx.logger.warning(f"Data fetching returned an error for session {session_id}: {result['error_message']}")
            return {
                "session_id": session_id,
                "message_type": "error",
                "content": result["error_message"]
            }
        
        # Format the response
        formatted_response = format_verifiable_data_response(result)
        
        return {
            "session_id": session_id,
            "message_type": "response",
            "content": formatted_response
        }
    except Exception as e:
        error_message = f"Error processing verifiable data request: {str(e)}"
        ctx.logger.error(f"{error_message} for session {session_id}")
        return {
            "session_id": session_id,
            "message_type": "error",
            "content": error_message
        } 