# Durable Approval Recovery Runtime (A2.38)

## Purpose

`A2.38` hardens COO confirmation flow with durable approval/idempotency records
and restart-safe replay recovery for `/api/v1/answer` diagnostics.

This milestone provides:

- durable approval session record contracts;
- durable idempotency record contracts;
- persistence wiring to memory store for durable records;
- token ttl and one-time confirmation guards;
- restart-safe deterministic idempotency replay recovery.

Safe-mode behavior is preserved: no real execution side effects.

## Contracts

Durable approval session contract version: `v1`
Idempotency record contract version: `v1`

Diagnostics contracts exposed:

- `assistant_durable_approval_session`
- `assistant_idempotency_record`
- `durable_approval_session_contract_version`
- `idempotency_record_contract_version`

## Durable record wiring

Records are persisted via memory store keys:

- `session:<sid>:durable:approval_session_record`
- `session:<sid>:durable:idempotency_record:last`
- `session:<sid>:durable:idempotency_record:<idempotency_key>`

Runtime flow:

1. Load durable records at request start (best effort).
2. Apply runtime transitions and guards.
3. Persist refreshed durable records at request end (best effort).

## Token guards

Durable token protection checks:

- `confirmation_token_expired`
- `confirmation_token_consumed`

If guard triggers, transition intent is blocked and handshake remains
`pending_confirmation`.

## Restart-safe replay recovery

Idempotency recovery checks prior durable record before in-memory map:

- same key + same fingerprint -> `replayed` with
  `idempotency_replay_recovered_from_durable`;
- same key + different fingerprint -> `conflict` (blocked transition).

This keeps replay behavior deterministic across process restarts.

## Feature flags

Runtime remains governed by assistant feature flags:

- `feature_assistant_mode=false`
- `feature_assistant_proactive=false`
- `feature_assistant_actions=false`

Defaults remain OFF and preserve base behavior.

## Quality gates

Release-gate docs checks validate:

- architecture markers for durable recovery contracts and guards;
- README reference to this runtime document;
- roadmap CI entry for A2.38 runtime docs quality gate.
