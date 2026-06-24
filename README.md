# saihm-crewai

**SAIHM memory for CrewAI — route CrewAI's memory through a store you own. Portable, encrypted, provably erasable.**

> ⭐ **[Star SAIHM on GitHub](https://github.com/SAIHM-Admin/saihm-mcp)** and share it — help every agent get portable, provable memory. [Share on X](https://x.com/intent/tweet?text=CrewAI%20with%20a%20memory%20you%20own%20-%20portable%2C%20encrypted%2C%20provably%20erasable%20-%20via%20SAIHM.&url=https%3A%2F%2Fgithub.com%2Fcitw2%2Fsaihm-crewai).

A runnable demo of [SAIHM](https://saihm.coti.global) as a [CrewAI](https://www.crewai.com/) storage backend. `SaihmStorageBackend` implements CrewAI's `StorageBackend` protocol, so you can route a crew's memory through SAIHM and get memory you actually own: portable across models *and* frameworks, non-custodial, and **provably erasable** (GDPR Art. 17). The same store opens from the core client, from this CrewAI backend, and from the [LangChain/LlamaIndex](https://github.com/citw2/saihm-langchain) and [AutoGen](https://github.com/citw2/saihm-autogen) adapters — one `forget` removes a memory from all of them at once.

**No Python cryptography.** All sealing happens in a small bundled **Node sidecar** (`server.mjs`, built on the same sealing client [`@saihm/mcp-server-pro`](https://www.npmjs.com/package/@saihm/mcp-server-pro) as [demo-claude-code](https://github.com/citw2/demo-claude-code)). Python drives it over [MCP](https://modelcontextprotocol.io) stdio and never holds a key — one audited crypto implementation, not a second one ported to Python.

## Run it

```
git clone https://github.com/citw2/saihm-crewai
cd saihm-crewai

npm install                                  # the Node sidecar (does the sealing)

python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python demo.py                               # offline blind sandbox; no account
```

You'll see the backend register through CrewAI's documented factory hook, three CrewAI records sealed into one store, exact recall and a client-side search, and then a `delete` that crypto-shreds a record — proving erasure, not just hiding it.

## Use it in your code

`SaihmStorageBackend` satisfies CrewAI's `StorageBackend` protocol. Wire it in once at startup with the documented factory hook, then select the `"saihm"` storage spec in your CrewAI memory configuration:

```python
from crewai.memory.storage.factory import set_memory_storage_factory
from saihm_memory import SaihmStorageBackend

# Route CrewAI's memory through SAIHM. Return None for specs you don't handle so
# CrewAI's built-in selection still works for everything else.
set_memory_storage_factory(lambda spec: SaihmStorageBackend() if spec == "saihm" else None)

# ... build your Crew with memory enabled and its storage spec set to "saihm".
# (local blind sandbox by default; set the SAIHM_* env below to go live)
```

Run from inside the cloned repo (the package locates its bundled Node sidecar relative to itself), or add the repo to your `PYTHONPATH`.

> Already on MCP? Any MCP host (Claude Code, Cursor, your own client) can use the same store directly via `npx @saihm/mcp-server` — see [demo-claude-code](https://github.com/citw2/demo-claude-code). This repo is the native CrewAI path.

### A note on retrieval (SAIHM is a *blind* store)

SAIHM's endpoint only ever holds ciphertext, so it cannot run a server-side vector index. Retrieval is therefore **client-side**: `search` ranks by cosine over the embedding CrewAI stored on each record (persisted in the sealed cell), and falls back to recency when no embedding is present (as in the offline demo). Exact recall (`get_record`, `list_records`) and **erasure** (`delete`, `reset` → crypto-shred) are always exact. That client-side boundary is the privacy guarantee, not a limitation to work around: the store you don't trust never sees your plaintext or your query.

## Why this matters

A per-vendor or per-framework "memory" locks your context in one place. SAIHM gives you memory that is:

1. **Yours / portable.** One live store grounds every model (Claude, GPT, DeepSeek, Qwen, Kimi, GLM, your own agent) **and** every framework adapter — no per-tool export, no lossy import.
2. **Non-custodial.** Every record is sealed client-side by the Node sidecar; the endpoint only ever holds ciphertext and never sees your keys. Python does no crypto.
3. **Provably erasable.** `delete`/`reset` crypto-shred records (each wrapped key is destroyed). They return nothing afterward and every consumer loses access at once — not a soft "hidden" flag. This is what GDPR Art. 17 actually asks for.

## Go live against the real SAIHM service

The local sandbox is a throwaway stand-in so you can try the protocol offline — it is **not** the SAIHM service and stores nothing beyond the current process. To run against the real, hosted, blind endpoint:

1. **Join SAIHM** at **[saihm.coti.global/join](https://saihm.coti.global/join)** and onboard to obtain your JWT. (Going live requires a paid membership — there is no free tier.)
2. Set the environment before running, and the same code goes live:

   ```
   export SAIHM_ENDPOINT_URL=https://saihm.coti.global/mcp
   export SAIHM_AUTH_HEADER="Bearer <your-onboard-JWT>"
   export SAIHM_MASTER_SECRET_HEX=<at least 64 hex chars, generated and held only by you>
   python demo.py
   ```

Your master secret never leaves your machine; the endpoint only ever receives ciphertext.

## How it works

- The bundled **Node sidecar** (`server.mjs`) exposes four MCP tools — `saihm_remember`, `saihm_recall`, `saihm_forget`, `saihm_status` — and seals every cell with [`@saihm/client-pro`](https://www.npmjs.com/package/@saihm/client-pro): an **ML-DSA-65** identity signs it, a per-cell **AES-256-GCM** key encrypts it, and that key is wrapped under a key-encryption key derived from *your* master secret. Sharing uses **ML-KEM-768**.
- [`SaihmMemoryClient`](./saihm_memory/client.py) spawns that sidecar once and keeps a single long-lived MCP session, exposing blocking `remember` / `recall` / `forget` / `status`. [`SaihmStorageBackend`](./saihm_memory/crewai_memory.py) maps each CrewAI `MemoryRecord` to one sealed cell over it (with async `asave`/`asearch`/`adelete` wrappers).
- Only opaque ciphertext leaves the sidecar. [`sandbox.mjs`](./sandbox.mjs) is a complete, readable *blind operator* for offline use: it stores and returns ciphertext and **never holds a key**.

## Built on / see also

- **[saihm-langchain](https://github.com/citw2/saihm-langchain)** — the same store for LangChain (`BaseChatMessageHistory`) and LlamaIndex (`BaseMemory`).
- **[saihm-autogen](https://github.com/citw2/saihm-autogen)** — the same store as an AutoGen `Memory`.
- **[demo-cross-model-memory](https://github.com/citw2/demo-cross-model-memory)** — one memory across Claude, DeepSeek, Qwen, Kimi, GLM, and GPT.
- **[demo-claude-code](https://github.com/citw2/demo-claude-code)** — the same sidecar as an MCP server for Claude Code, Cursor, and any MCP host.
- **[All demos + landing page](https://citw2.github.io/saihm-demos/)**.
- **Learn more:** [AI memory needs a standard](https://saihm.coti.global/blog/2026-05-18-ai-memory-needs-a-standard) · [What makes SAIHM different](https://saihm.coti.global/blog/2026-05-31-what-makes-saihm-different).
- **Join the protocol:** [saihm.coti.global/join](https://saihm.coti.global/join).

## License

Apache-2.0 © SAIHM
