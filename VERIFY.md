# Verification Checklist (Contracts)

This document maps the project constraints to the specific files, modules, and observable behaviors implemented in the codebase.

- [x] **req-1-chat-endpoint**: The service exposes a conversational API endpoint at `POST /v1/chat` (see `src/api.py`). It returns the `reply` and `active_topic`.
- [x] **req-2-context-persistence**: The `ContextManager.save_state()` explicitly writes the session's context to `logs/context_{session_id}.json` after every API call (see `src/context_engine.py`).
- [x] **req-3-entity-extraction-pinning**: The system utilizes Regex (`r'IT-\d{4}'`) to dynamically identify ticket IDs and extract them to `self.state["pinned"]` (see `src/context_engine.py`).
- [x] **req-4-token-budget-eviction**: `ContextManager.prune_recent()` actively applies a FIFO rolling window token limit by measuring token length with `tiktoken` against the `TOKEN_BUDGET_LIMIT`.
- [x] **req-5-topic-tracking**: The system calls a fast LLM configured with JSON structured outputs to infer and update `active_topic` dynamically based on user focus (see `extract_topic` in `src/llm_client.py`).
- [x] **req-6-five-turn-eval-script**: Included `eval_5_turns.py` at the root, which runs a sequence proving context pinning and topic switching work natively while proving that older messages were explicitly evicted.
- [x] **req-7-docker-compose-setup**: Standard `Dockerfile` and `docker-compose.yml` are provided at root for a fully containerized one-command startup.
- [x] **req-8-env-config**: `.env.example` lists the required variables `TOKEN_BUDGET_LIMIT` and `GROQ_API_KEY`.
- [x] **req-9-context-retrieval-api**: A dedicated endpoint `GET /v1/context/{session_id}` has been created to retrieve the current session's memory (see `src/api.py`).
- [x] **req-10-graceful-error-handling**: Inside `ContextManager.process_message()`, if the LLM fails during generation, the `user_message` is safely popped from `recent` and reverted using a `try-except` block, preventing corrupted session states.
