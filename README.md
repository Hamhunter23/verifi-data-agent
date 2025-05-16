# Verifi-Data-Agent

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:domain/dataservices](https://img.shields.io/badge/domain-dataservices-blue)
![tag:domain/crypto](https://img.shields.io/badge/domain-crypto-orange)
![tag:domain/api_integration](https://img.shields.io/badge/domain-api_integration-green)
![tag:domain/llm](https://img.shields.io/badge/domain-llm-purple)

## Overview

This AI Agent bridges decentralized applications with verifiable, real-world data. It leverages Google's Gemini LLM for natural language understanding, allowing users to query complex information through simple chat interactions. The agent provides access to multiple types of verified data:

1. **Cryptocurrency Prices**: Real-time market data from CoinGecko API
2. **Education Credentials**: Verified academic and professional certifications
3. **Supply Chain Status**: Product origin and journey tracking information
4. **Carbon Footprint**: Environmental impact data for products, companies, and activities
5. **Reputation Scores**: Trust metrics for developers, services, and DAOs

The core problem this agent addresses is the difficulty users and protocols face in accessing, verifying, and integrating crucial off-chain information reliably and automatically into decentralized systems.

## Features

* Natural language query processing via Google Gemini
* Intelligent entity type detection (no need to specify technical parameters)
* Multiple data types with specialized verification mechanisms
* Case-insensitive identifier matching for improved user experience
* Modular design for easy extension to new data sources
* Includes Quota and Health Check protocols for robustness

## Project Structure

```
.
├── main_agent.py               # Core VerifiableDataAgent logic
├── chat_protocol_integration.py  # Handles chat messages & Gemini API interaction for NLU
├── data_source_handler.py      # Routes requests to appropriate data handlers
├── crypto_price.py             # Fetches cryptocurrency price data
├── education_credentials.py    # Handles education credential verification
├── supply_chain.py             # Manages supply chain tracking data
├── carbon_footprint.py         # Provides environmental impact information
├── reputation_score.py         # Delivers trust metrics for entities
├── models.py                   # Pydantic models for requests/responses
├── demo_client.py              # CLI client to interact with VerifiableDataAgent
├── README.md                   # This file
├── requirements.txt            # Python package dependencies
└── .env.example                # Example for environment variable configuration
```

## Setup and Running

**1. Prerequisites:**

* Python 3.8+
* A valid Google Gemini API Key

**2. Clone the Repository (if applicable):**

   ```bash
   git clone https://github.com/Hamhunter23/verifi-data-agent.git
   cd verify-data-agent
   ```

**3. Create and Configure Environment Variables:**

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and add your details:

   * `GEMINI_API_KEY` (Required): Your Google Gemini API key
   * `GEMINI_MODEL_NAME` (Optional): Defaults to `gemini-1.5-pro`
   * `VERIFIABLE_DATA_AGENT_MAILBOX_KEY` (Optional): For a persistent mailbox ID on Agentverse
   * `TARGET_VERIFIABLE_DATA_AGENT_ADDRESS` (Optional for demo): Address of the deployed agent
   * `DEMO_CLIENT_SEED` (Optional): Seed for the demo client agent

**4. Install Dependencies:**

   It's recommended to use a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

**5. Run the VerifiableDataAgent:**

   In one terminal, start the main agent:
   ```bash
   python main_agent.py
   ```

**6. Run the Demo Client:**

   In a separate terminal:
   ```bash
   python demo_client.py
   ```

## Usage Examples

The agent now supports a wide range of natural language queries:

### Cryptocurrency Prices
* "What is the current price of Bitcoin?"
* "How much is Ethereum worth in euros?"
* "What's the price of Fetch.ai token?"

### Education Credentials
* "Show me John Smith's education credentials"
* "What certifications does Jane Doe have?"
* "Verify Alex Chen's Fetch.ai developer certification"

### Supply Chain Information
* "Where does the Costa Rica coffee come from?"
* "Show me the supply chain for EcoPhone X1"
* "Track the journey of the Costa Rica coffee"

### Carbon Footprint Data
* "What's the carbon footprint of MacBook Pro?"
* "Tell me about GreenCorp's emissions"
* "What's the carbon impact of a London to NYC flight?"
* "How much carbon is produced by California electricity?"

### Reputation Scores
* "What's Alex Rodriguez's developer reputation?"
* "Show me the reputation of DecentraGov DAO"
* "How reliable is the TrustData Verification Service?"

## Extensibility

To add new data sources or types:

1. Create a new module (e.g., `new_data_type.py`) with a `fetch_new_data_type` function
2. Update `data_source_handler.py` to import and route to your new function
3. Update the Gemini prompt in `chat_protocol_integration.py` to recognize the new data type
4. Add any necessary normalization functions for identifiers

## Future Enhancements

* Integration with real-world data sources and oracle networks
* Implementation of cryptographic verification mechanisms
* Support for more complex queries and data relationships
* Enhanced caching and performance optimizations
* User preference settings for data sources and verification levels

## Hackathon Compliance

This project meets the hackathon requirements:

*   **Agent-First**: Implemented using `uAgents`, featuring a primary `VerifiableDataAgent` that orchestrates data fetching, LLM interaction, and communication.
*   **LLM-Native**: Seamlessly powered by Google Gemini for natural language understanding of user queries. Designed for integration with ASI1-mini as the user-facing chat interface.
*   **User-Focused**: Provides an intuitive way for users to access real-world data through natural language. Responses are clear, timestamped, and include source descriptions for transparency.

## Interaction Flow (with Demo Client)

1.  User runs `demo_client.py`.
2.  User inputs the address of the running `VerifiableDataAgent` (or it's loaded from `.env`).
3.  User types a natural language query into the `demo_client.py` console.
4.  `demo_client.py` sends a `ChatMessage` to the `VerifiableDataAgent`.
5.  The `VerifiableDataAgent` (`main_agent.py` + `chat_protocol_integration.py`) processes the query:
    *   Calls Google Gemini to parse the query into a structured `VerifiableDataRequest`.
    *   Sends this request internally to its data fetching handler.
6.  The handler in `main_agent.py` calls `fetch_verifiable_data` (in `data_source_handler.py`).
7.  `data_source_handler.py` calls the CoinGecko API.
8.  The data is returned as a `VerifiableDataResponse`.
9.  `main_agent.py` formats this into a human-readable string.
10. This string is sent back as a `ChatMessage` to `demo_client.py`.
11. `demo_client.py` prints the formatted response to the console.

This simulates the interaction that would occur if using ASI1-mini as the front-end chat interface.

## Usage Examples for Demo

When running `demo_client.py`:

*   **Query:** "What is the price of Bitcoin in USD?"
*   **Query:** "Can you tell me the price of ethereum in eur?"
*   **Query:** "Fetch crypto_price for fetch-ai vs_currency=gbp"
*   **Query:** "current price of solana in usd"

## Troubleshooting

*   **Check Logs**: Both `main_agent.py` and `demo_client.py` print logs.
*   **API Keys**: Ensure `GEMINI_API_KEY` is correctly set in the `.env` file for `main_agent.py`.
*   **Agent Address**: Ensure you provide the correct address of the running `VerifiableDataAgent` to `demo_client.py`.
*   **Network Issues**: Verify connectivity to CoinGecko and Google APIs.
*   **Dependencies**: `pip install -r requirements.txt` in your virtual environment.

**Example Chat Queries (for ASI1-mini):**

*   "What is the price of Bitcoin?"
*   "Can you tell me the price of ethereum in eur?"
*   "Fetch crypto_price for fetch-ai vs_currency=gbp"

**Direct Agent Interaction (Structured):**

While primarily designed for chat via ASI1-mini, the agent can also technically handle direct `VerifiableDataRequest` messages if sent by another agent (though this bypasses the Gemini LLM parsing).

*   **Request Model**: `VerifiableDataRequest` (from `models.py`)
*   **Response Model**: `VerifiableDataResponse` or `ErrorMessage` (from `models.py` and `uagents_core.models`)

**Setup & Running:**

1.  Ensure you have the necessary Python packages: `uagents`, `httpx`, `google-generativeai`.
    ```bash
    pip install uagents httpx google-generativeai
    ```
2.  Set the `VERIFIABLE_DATA_AGENT_MAILBOX_KEY` environment variable if you want a persistent mailbox ID (optional, a default is provided).
3.  **Crucially, set the `GEMINI_API_KEY` environment variable with your valid Google Gemini API key.**
4.  Optionally, set `GEMINI_MODEL_NAME` environment variable (defaults to `gemini-1.5-flash-latest`).
5.  Run `python main_agent.py`.

**Protocols Exposed:**

*   `VerifiableDataChatProtocol` (for ASI1-mini and chat interactions, uses Gemini internally)
*   `VerifiableDataQuotaProtocol` (for direct request rate limiting)
*   `VerifiableDataHealthProtocol` (for health checks)

This agent leverages the Fetch.ai ecosystem and Google Gemini to provide a robust solution for accessing real-world data in a decentralized context, fitting the goals of the hackathon. 
