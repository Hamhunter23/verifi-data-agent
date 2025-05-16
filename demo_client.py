import asyncio
from datetime import datetime, timezone
from uuid import uuid4
import os

from uagents import Agent, Context, Model, Protocol
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Configuration
CLIENT_AGENT_SEED = os.environ.get("DEMO_CLIENT_SEED", "verifiable_data_demo_client_seed")
TARGET_AGENT_ADDRESS_STORE = {"address": os.environ.get("TARGET_VERIFIABLE_DATA_AGENT_ADDRESS", "")} 

# --- Models for internal command --- 
class SendUserQuery(Model):
    user_query: str
    target_agent_address: str

# Define the chat protocol for the client
client_chat_proto = Protocol(name="ClientChatProto", version="1.2", spec=chat_protocol_spec)

# Client Agent
client_agent_instance = Agent(
    name="DemoClientAgent",
    seed=CLIENT_AGENT_SEED,
    # port=8002, # Optional: if you want to inspect it or have it receive other messages
    # mailbox=f"{CLIENT_AGENT_SEED}@https://agentverse.ai", # Optional: if it needs a mailbox
)
fund_agent_if_low(client_agent_instance.wallet.address())

@client_agent_instance.on_event("startup")
async def initial_startup_message(ctx: Context):
    ctx.logger.info(f"Demo Client Agent registered with address: {ctx.agent.address}")
    # Initial message to user is now handled by run_demo_interaction_loop after address input

@client_chat_proto.on_message(ChatMessage)
async def handle_response_message(ctx: Context, sender: str, msg: ChatMessage):
    # ctx.logger.info(f"Response received from VerifiableDataAgent ({sender}):")
    full_response_text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            full_response_text += item.text + "\n"
        elif isinstance(item, EndSessionContent):
            print("(Session ended by agent)")
    print(f"\nAGENT RESPONSE:\n-------------------\n{full_response_text.strip()}\n-------------------")
    print("\nEnter your next query (or type 'exit'): ")

@client_chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Acknowledgement received from {sender} for message: {msg.acknowledged_msg_id}")

client_agent_instance.include(client_chat_proto)

# Handler for the internal command to send a message
@client_agent_instance.on_message(SendUserQuery)
async def handle_send_user_query_command(ctx: Context, _sender: str, command: SendUserQuery):
    ctx.logger.info(f"Internal command to send query: '{command.user_query}' to {command.target_agent_address}")
    message_content = [
        StartSessionContent(type="start-session"),
        TextContent(type="text", text=command.user_query)
    ]
    chat_msg_to_send = ChatMessage(
        timestamp=datetime.now(timezone.utc),
        msg_id=uuid4(),
        content=message_content
    )
    await ctx.send(destination=command.target_agent_address, message=chat_msg_to_send)
    # User feedback is now handled in the interaction loop or by response handler
    print(f"Sent query: '{command.user_query}' to {command.target_agent_address}")
    print("Waiting for response...")

async def run_demo_interaction_loop(startup_ctx: Context): 
    target_address = TARGET_AGENT_ADDRESS_STORE["address"]
    if not target_address:
        # Use startup_ctx.logger if available, otherwise print
        log_func = startup_ctx.logger.info if hasattr(startup_ctx, 'logger') else print
        target_address = await asyncio.to_thread(input, "Enter the address of the VerifiableDataAgent: ")
        target_address = target_address.strip()
        TARGET_AGENT_ADDRESS_STORE["address"] = target_address # Store it for the handler
    
    if not target_address:
        print("No target agent address provided. Exiting.")
        return

    print(f"\nDemo Client for VerifiableDataAgent")
    print(f"Targeting agent: {target_address}")
    print("Type your queries below. Type 'exit' or 'quit' to stop.")
    print("\nEnter your first query (or type 'exit'): ")

    while True:
        try:
            user_query = await asyncio.to_thread(input, "") 
            if user_query.lower() in ['exit', 'quit']:
                print("Exiting demo client.")
                break
            if not user_query:
                continue
            
            # Create the internal command and send it to self
            command_to_send_internally = SendUserQuery(
                user_query=user_query,
                target_agent_address=target_address # Pass target address in command
            )
            # Use the passed startup_ctx to send the internal command to self
            await startup_ctx.send(client_agent_instance.address, command_to_send_internally)
            # The print statements for "Sent query" and "Waiting" are now in the handler

        except KeyboardInterrupt:
            print("\nExiting demo client (KeyboardInterrupt).")
            break
        except Exception as e:
            print(f"An error occurred in demo loop: {e}. Loop continues.")

if __name__ == "__main__":
    @client_agent_instance.on_event("startup")
    async def client_startup_and_run_demo(ctx: Context):
        ctx.logger.info(f"Demo Client Agent {ctx.agent.address} starting up...") 
        # Pass the current context (ctx) to the interaction loop
        asyncio.create_task(run_demo_interaction_loop(ctx))

    client_agent_instance.run() 