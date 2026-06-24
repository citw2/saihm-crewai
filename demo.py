#!/usr/bin/env python3
"""SAIHM memory for CrewAI — route CrewAI's memory through a store you own, with erasure you can prove.

    npm install                 # the Node sidecar that does the client-side sealing
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python demo.py              # runs offline against a local blind sandbox; no account

Go live (paid membership, no free tier) by pointing it at the hosted, blind endpoint:
    export SAIHM_ENDPOINT_URL=https://saihm.coti.global/mcp
    export SAIHM_AUTH_HEADER="Bearer <your-onboard-JWT>"
    export SAIHM_MASTER_SECRET_HEX=<at least 64 hex chars, generated and held only by you>
Your master secret never leaves your machine; the endpoint only ever sees ciphertext.
"""
import os

from crewai.memory.storage.backend import StorageBackend
from crewai.memory.storage.factory import resolve_memory_storage, set_memory_storage_factory
from crewai.memory.types import MemoryRecord

from saihm_memory import SaihmMemoryClient, SaihmStorageBackend


def rule():
    print("-" * 72)


def main():
    live = bool(os.environ.get("SAIHM_ENDPOINT_URL"))
    client = SaihmMemoryClient()  # one store; reads SAIHM_* env for live mode automatically
    backend = SaihmStorageBackend(client=client)
    try:
        rule(); print("SAIHM memory for CrewAI"); rule()
        print("endpoint :", "hosted SAIHM (LIVE)" if live else "local blind sandbox")
        print("status   :", client.status())
        print("custody  : non-custodial (the endpoint stores ciphertext only; it holds no key)")
        print("backend  : implements crewai StorageBackend protocol:", isinstance(backend, StorageBackend))
        print()

        # How you wire it into CrewAI — the documented factory hook. No LLM needed to show it
        # resolves: register once at startup, then the "saihm" storage spec routes through SAIHM.
        set_memory_storage_factory(lambda spec: backend if spec == "saihm" else None)
        print('register : resolve("saihm") routes to our backend:', resolve_memory_storage("saihm") is backend)
        print('         : resolve("other") is None (defers to built-in):', resolve_memory_storage("other") is None)
        print()

        # 1) Save three personal facts as CrewAI MemoryRecords (sealed client-side).
        rule(); print("(1) save() — three CrewAI records, sealed into SAIHM:"); rule()
        facts = [
            "My name is Dana Okafor.",
            "I am allergic to penicillin.",
            "I am building a Rust ray tracer called Lumen.",
        ]
        backend.save([MemoryRecord(content=f, scope="/demo/dana", categories=["personal"]) for f in facts])
        print(f"Sealed {backend.count()} records. list_records (newest first):")
        for r in backend.list_records():
            print(f"   - {r.content}  [id={r.id[:8]} scope={r.scope}]")
        print()

        # 2) Retrieval. SAIHM is blind, so ranking is client-side; exact recall is exact.
        rule(); print("(2) search() + get_record():"); rule()
        hits = backend.search(query_embedding=[], scope_prefix="/demo", limit=3)
        print("search('/demo') returns", len(hits), "records (recency-ranked offline):")
        for r, s in hits:
            print(f"   - {r.content}  (score={s:.2f})")
        pen = next(r for r in backend.list_records() if "penicillin" in r.content)
        print("get_record(id) ->", backend.get_record(pen.id).content)
        print()

        # 3) Provable erasure — delete crypto-shreds; the record is gone, not hidden.
        rule(); print("(3) delete() — crypto-shred the medical record:"); rule()
        removed = backend.delete(record_ids=[pen.id])
        print(f"delete(record_ids=[{pen.id[:8]}...]) removed {removed} record(s) (crypto-shredded).")
        print("count now:", backend.count())
        print("get_record(that id) now returns:",
              "NOTHING (crypto-shredded)" if backend.get_record(pen.id) is None else "STILL PRESENT (unexpected)")
        assert backend.get_record(pen.id) is None, "erasure failed"
        print()

        # 4) reset() crypto-shreds the rest of the scope, too.
        backend.reset(scope_prefix="/demo")
        print("after reset('/demo'), records remaining:", backend.count())
        print()

        rule()
        print("CrewAI memory, in a store you own — with erasure you can prove.")
        print("Go live (paid): https://saihm.coti.global/join")
        rule()
    finally:
        set_memory_storage_factory(None)
        client.close()


if __name__ == "__main__":
    main()
