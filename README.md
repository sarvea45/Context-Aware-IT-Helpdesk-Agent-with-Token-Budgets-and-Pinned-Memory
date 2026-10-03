# Context-Aware IT Helpdesk Agent

A production-grade conversational AI agent designed for IT Helpdesk scenarios. This project demonstrates advanced **Context Engineering**, solving the "context amnesia" problem common in standard LLM wrappers by explicitly managing the conversational token window.

## Architecture

This agent does not simply append messages until the API throws an error. It uses a structured `ContextManager` that divides memory into three discrete components:
1. **`pinned`**: A permanent key-value store for critical entities (like `ticket_id`). This memory completely bypasses token eviction and is always injected into the system prompt.
2. **`recent`**: A rolling window of the conversational history.
3. **`active_topic`**: Dynamically inferred state representing the user's current intent.

### Token Budgeting & Eviction
The system enforces token limits using strict byte-pair encoding (BPE) via the `tiktoken` library. When the total tokens in the `recent` array exceed the configured `TOKEN_BUDGET_LIMIT`, the oldest messages are explicitly evicted using a First-In-First-Out (FIFO) algorithm.

## Setup & Installation

1. Clone the repository and configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env to add your actual GROQ_API_KEY
   ```
2. Start the application using Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
   *The API and Healthcheck will be exposed on port `8000`.*

## Verification & Evaluation

To mathematically prove the context mechanism works (i.e. that older messages fall off while pinned items remain), we provide a 5-turn evaluation script. 

This script deliberately overrides the token limit to an extremely low threshold (100 tokens) on Turn 3. This forces the explicit eviction of Turn 1 and Turn 2. The script then asserts that the Agent is still able to recall the `ticket_id` mentioned in Turn 2, because the extraction engine successfully moved it to `pinned` memory.

1. Ensure the API is running, then run the evaluation script:
   ```bash
   pip install requests
   python eval_5_turns.py
   ```
2. **Observability:** Check the logs generated in the `./logs/` directory. After every turn, the API explicitly dumps the exact state of the context to disk (e.g., `logs/context_{session_id}.json`) for inspection.
