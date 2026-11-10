---
Area: Implementation
datetime_stamp: 2026-10-14T00:00:00-05:00
status: in-progress
confidence: vetted
tags:
  - implementation
  - impulse-engine
  - activation-engine
  - continuity
  - architecture
links:
  - "[[Implementation Index]]"
summary: Runtime architecture diagrams for the Impulse Engine, Activation Engine, and Continuity layer.
canonical: true
---

# Impulse Engine Architecture Diagrams

These diagrams describe the current runtime shape of the Impulse Engine, the
optional Activation Engine, and the Continuity layer.

## Whole System

```mermaid
flowchart LR
    host["Host agent or adapter"]
    hermes["Hermes plugin"]
    core["Impulse Engine core"]
    activation["Activation Engine"]
    continuity["Continuity layer"]
    source["Markdown source material"]
    index["Local vector index"]

    host -->|"activity and idle heartbeat"| hermes
    hermes -->|"record activity, seed, pulse, claim, ack"| core
    hermes -->|"user and response observations"| continuity
    hermes -->|"claim source-grounded proposal"| continuity
    continuity -->|"focused vector request"| activation
    activation -->|"candidate or proposal material"| continuity
    source -->|"ingested atoms"| activation
    activation -->|"embed and query"| index
    activation -->|"fallback candidate"| hermes
    core -->|"reflection context"| hermes
    hermes -->|"brief reflection or NO_REPLY"| host
```

The core is deliberately small. Activation knows source material, Continuity
knows recent conceptual threads, and the Hermes adapter decides when to connect
those layers to an idle reflection turn.

## Impulse Engine Core

```mermaid
flowchart TD
    seed["PotentialSeed"]
    pool["Potential pool"]
    activity["Host activity"]
    idle["Idle timer"]
    pulse["pulse"]
    choose["Weighted potential selection"]
    pending["Pending impulse outbox"]
    claim["Claim lease"]
    ack["Acknowledgement"]
    expire["Claim expiry"]

    seed -->|"seed"| pool
    seed -->|"optional"| activity
    activity -->|"restart"| idle
    idle -->|"idle timeout reached"| pulse
    pool --> pulse
    pulse -->|"cooldown satisfied"| choose
    choose -->|"remove potential"| pending
    pending -->|"claim by consumer"| claim
    claim -->|"engaged, declined, acted"| ack
    claim -->|"ttl elapsed"| expire
    expire -->|"requeue impulse"| pending
```

The core holds temporary potentials and emits at most one pending impulse per
pulse. Leases keep delivery explicit: consumers claim an impulse and later
acknowledge the outcome; expired claims return to the pending outbox.

## Activation Engine

```mermaid
flowchart TD
    root["Registered Markdown source"]
    scan["Recursive Markdown scan"]
    atoms["Heading-aware source atoms"]
    checkpoint["File hash checkpoints"]
    embed["FastEmbed embeddings"]
    chroma["Chroma persistent index"]
    field["Activation field"]
    strike["Lightning strike"]
    neighborhood["Semantic neighborhood"]
    candidate["Candidate queue"]
    diagnostics["Diagnostics and journal"]
    adapter["Delivery adapter"]

    root --> scan
    scan --> atoms
    atoms --> checkpoint
    checkpoint -->|"new or changed atoms"| embed
    embed --> chroma
    chroma -->|"sample anchors"| field
    field -->|"novelty, dormancy, residue"| strike
    chroma -->|"neighbors"| neighborhood
    strike --> neighborhood
    neighborhood -->|"resonance or synthesis"| candidate
    candidate -->|"claim and acknowledge"| adapter
    scan --> diagnostics
    strike --> diagnostics
    candidate --> diagnostics
```

Ingestion is incremental. A bounded strike starts from one selected source
anchor, inspects one semantic neighborhood, and emits at most one candidate
with source provenance and diagnostic evidence.

## Continuity Layer

```mermaid
flowchart TD
    observation["CognitiveTrace"]
    embed["Observation embedding"]
    field["ContinuityField"]
    match["Nearest thread match"]
    thread["Continuity thread"]
    rank["Attention ranking"]
    act["Cognitive act"]
    claim["Attention claim"]
    coordinator["CognitionCoordinator"]
    activation["Activation Engine focused strike"]
    proposal["Source-grounded proposal"]
    impulse["Impulse Engine seed"]
    reflection["Idle reflection"]
    weak_trace["Weak reflection trace"]
    ack["Attention acknowledgement"]

    observation --> embed
    embed --> field
    field --> match
    match -->|"similar enough"| thread
    match -->|"new pattern"| thread
    thread -->|"salience, recurrence, dormancy"| rank
    rank --> act
    act -->|"interrogate, integrate, sustain"| claim
    claim --> coordinator
    coordinator -->|"focus vector"| activation
    activation -->|"grounded candidate material"| proposal
    proposal --> impulse
    impulse --> reflection
    reflection -->|"engaged"| weak_trace
    weak_trace -->|"low amplification"| field
    reflection --> ack
    ack --> field
```

Continuity stores compact traces rather than full conversations. Similar traces
merge into threads; recurrence and salience decide whether a thread becomes
attention-worthy. An engaged idle reflection returns as a weak trace, preserving
the possibility of later reinforcement without demanding immediate follow-up.

## Idle Reflection Loop

```mermaid
sequenceDiagram
    participant User
    participant Hermes
    participant Core as Impulse Engine
    participant Continuity
    participant Activation

    User->>Hermes: Normal message
    Hermes->>Core: record_activity
    Hermes->>Continuity: observe user trace
    Hermes->>Continuity: observe assistant response

    Note over Hermes: Later, marked heartbeat fires

    Hermes->>Continuity: claim proposal
    Continuity->>Activation: directed strike from focus vector
    Activation-->>Continuity: grounded candidate material
    Continuity-->>Hermes: cognition proposal
    Hermes->>Core: seed structured cognition without resetting idleness
    Hermes->>Core: pulse and claim
    Core-->>Hermes: reflection context
    Hermes-->>User: brief reflection or NO_REPLY
    Hermes->>Core: acknowledge claim
    Hermes->>Continuity: acknowledge proposal
    Hermes->>Continuity: record engaged reflection as weak trace
```
