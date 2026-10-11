

Here's a diagram that reflects what the code actually does — making implicit dependencies visible and flagging the structural hazards from the analysis:





```mermaid
graph TB
    %% ===== ENTRY =====
    subgraph ENTRY["Entry Points"]
        CLI["CLI<br/><i>genesis_measure.py --flags</i>"]
        UI["Tkinter UI<br/><i>genesis_measure.py (no args)</i>"]
    end

    %% ===== MODES =====
    subgraph MODES["Experiment Modes — all wrap run_single()"]
        SINGLE["run_single_mode"]
        MULTI["run_multi_seed<br/><i>N seeds, same params</i>"]
        SWEEP["run_sweep_kappa<br/><i>vary kappa, fixed seed</i>"]
        COMPARE["run_compare_geometry<br/><i>kappa=0 vs kappa&gt;0</i>"]
    end

    %% ===== run_single (the harness) =====
    subgraph RUN_SINGLE["run_single() — measurement harness"]
        INIT["seed RNG → GenesisState(N, dt)"]
        LOOP["Frame loop 1..n_frames<br/><i>every log_interval:<br/>|m|, vortices, histogram</i>"]
        FINAL["Post-loop derived metrics<br/><i>⚠️ recomputes detF from state.ux/uy<br/>(duplicates compression_rule)</i>"]
        INIT --> LOOP --> FINAL
    end

    %% ===== step() the orchestrator =====
    subgraph STEP_CALL["step(state, params, RULES, post) — core.py"]
        ZERO["torque_total ← zeros<br/>extra ← {}"]
        ITER["for rule in rules:<br/><i>each may mutate state,<br/>write to extra,<br/>contribute torque</i>"]
        POST_CALL["post(torque_total, state, params, extra)<br/><i>= locking_postprocess (optional hook)</i>"]
        UPDATE["state.theta ← (theta + dt · torque_total) mod 2π"]
        ZERO --> ITER --> POST_CALL --> UPDATE
    end

    %% ===== ACTIVE rule pipeline =====
    subgraph RULES_ACTIVE["Active Rule Pipeline (genesis_measure.py) — ORDER IS LOAD-BEARING"]
        direction TB
        R1["<b>1. alignment_rule</b><br/>━━━━━━━━━━<br/>writes extra[grad_align], extra[dtheta_align]<br/>returns: α · Σ sin(θₙ − θ)"]
        R2["<b>2. compression_rule</b> &nbsp;⚠️ god-module<br/>━━━━━━━━━━<br/>reads extra[grad_align]<br/>mutates state.tau, ux, uy, C<br/>writes extra[detF], extra[C]<br/>returns: 0.1 · tau"]
        R3["<b>3. curvature_rule</b><br/>━━━━━━━━━━<br/>reads state.ux/uy <i>(already mutated!)</i><br/>writes extra[curv_mag], extra[phi_curv]<br/>returns: κ_c · ‖∇²u‖ · sin(φ_c − θ)"]
        POST_RULE["<b>locking_postprocess</b> (post= hook)<br/>━━━━━━━━━━<br/>reads extra[C], extra[phase_torque]*, extra[tri_torque]*<br/>amplifies phase/tri torques where C high<br/>scales total torque by (1 − lock · C)<br/><i>*never present in 3-rule pipeline</i>"]

        R1 -->|"extra[grad_align]"| R2
        R2 -->|"state.ux/uy/C<br/>extra[C]"| R3
        R2 -.->|"extra[C]"| POST_RULE
    end

    %% ===== UNUSED but available rules =====
    subgraph RULES_UNUSED["Rules available in package but NOT in measure pipeline"]
        EX_PHASE["rules_phase.phase_rule<br/><i>writes extra[phase_torque]</i>"]
        EX_DIPOLE["rules_dipoles.dipole_rule"]
        EX_TRIAD["rules_triads.triad_rule<br/><i>writes extra[tri_torque]</i>"]
        EX_TRIAD_R["rules_triads_relative<br/><i>⚠️ same extra key as triads,<br/>no selector — choice = which import</i>"]
        EX_RELAX["relax.relaxation_rule<br/><i>⚠️ duplicates compression_rule's<br/>state mutations on tau/ux/uy</i>"]
        ADAPTER["GenesisGridEngine (adapter.py)<br/><i>uses a DIFFERENT default<br/>7-rule pipeline</i>"]
    end

    %% ===== STATE =====
    subgraph STATE["GenesisState — mutable, shared"]
        S_THETA["theta (N×N) — orientation"]
        S_TAU["tau (N×N) — tension"]
        S_UV["ux, uy (N×N) — displacement"]
        S_C["C (N×N) — compression"]
        S_XY["X, Y (N×N) — base grid"]
    end

    %% ===== PARAMS =====
    PARAMS["<b>GenesisParams</b><br/><i>flat bag of 18 knobs<br/>no grouping, no validation,<br/>no per-rule namespacing</i>"]

    %% ===== BACKEND (cross-cutting) =====
    BACKEND["<b>backend.py</b><br/>xp = numpy or cupy<br/><i>env: GENESIS_USE_CUPY<br/>imported by every module</i>"]

    %% ===== DIAGNOSTICS (out of pipeline) =====
    DIAG["<b>diagnostics.py</b><br/><i>read-only, NOT in step() pipeline<br/>detect_vortices, compute_unity</i>"]

    %% ===== OUTPUT =====
    subgraph OUTPUT["Output (results/)"]
        JSON["Per-run JSON<br/><i>time series, histogram,<br/>correlation, geometry</i>"]
        CSV["Summary CSV<br/><i>⚠️ header + row format<br/>hand-written, must stay in sync</i>"]
        CONSOLE["Console dashboards<br/><i>ASCII tables, live progress</i>"]
    end

    %% ===== CONNECTIONS =====
    CLI --> MODES
    UI --> MODES
    SINGLE --> RUN_SINGLE
    MULTI -->|loop seeds| RUN_SINGLE
    SWEEP -->|loop kappa| RUN_SINGLE
    COMPARE -->|loop: flat → geom| RUN_SINGLE

    LOOP -->|each frame| STEP_CALL
    LOOP -->|every log_interval| DIAG
    ITER --> RULES_ACTIVE

    RULES_ACTIVE -.reads & mutates.-> STATE
    STEP_CALL -.reads.-> PARAMS
    RULES_ACTIVE -.reads.-> PARAMS

    BACKEND -.-> STATE
    BACKEND -.-> RULES_ACTIVE
    BACKEND -.-> STEP_CALL

    FINAL --> OUTPUT
    LOOP --> OUTPUT
    MODES --> CONSOLE

    %% ===== STYLING =====
    classDef entry fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d
    classDef modes fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef run fill:#faf5ff,stroke:#7c3aed,stroke-width:2px,color:#3b0764
    classDef step fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12
    classDef rules fill:#fef3c7,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef unused fill:#fafafa,stroke:#a3a3a3,stroke-width:1px,stroke-dasharray:4 3,color:#525252
    classDef state fill:#f0fdfa,stroke:#0d9488,stroke-width:2px,color:#134e4a
    classDef cross fill:#fdf2f8,stroke:#db2777,stroke-width:1px,color:#831843
    classDef output fill:#f8fafc,stroke:#64748b,stroke-width:1px,color:#334155

    class ENTRY entry
    class MODES modes
    class RUN_SINGLE run
    class STEP_CALL step
    class RULES_ACTIVE rules
    class RULES_UNUSED unused
    class STATE,PARAMS state
    class BACKEND,DIAG cross
    class OUTPUT output
```

## What changed and why

**Made implicit dependencies visible.** Each rule now lists what it _reads from_, _mutates_, _writes to extra_, and _returns_ — so you can see at a glance why reordering the list breaks things. The labeled arrows between R1→R2→R3 show exactly which keys flow through `extra`.

**Separated "returns torque" from "mutates state".** `alignment_rule` is pure (returns torque only). `compression_rule` mutates four state fields _and_ returns torque. The diagram now treats those as different behaviors instead of glossing over them.

**Showed both pipelines.** The active 3-rule pipeline used by `genesis_measure.py` is in the bright box; the 7-rule adapter default and the orphaned rules are in the dashed-grey "available but unused" box so it's obvious there are two parallel realities.

**Surfaced the cross-cutters.** `backend.py` (numpy/cupy switch) and `diagnostics.py` (out-of-pipeline read-only) are now visible as their own concerns instead of being hidden.

**Flagged the duplication.** Arrows from `FINAL` and notes on `compression_rule` vs `relaxation_rule` make the duplicated `detF` / `tau`/`ux`/`uy` logic explicit.

**Honest about `locking_postprocess`.** Showed that two of its three inputs (`phase_torque`, `tri_torque`) are never produced by the active pipeline — the lock currently only freezes torque, it doesn't amplify anything.

Want me to save this to a markdown file in your repo (e.g. `genesis_engine_architecture.md`) so it doesn't overwrite the existing `architecture.md`?