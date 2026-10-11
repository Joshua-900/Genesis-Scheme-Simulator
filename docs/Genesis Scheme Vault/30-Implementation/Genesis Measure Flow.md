---
Area: Implementation
datetime_stamp: 2026-04-14T00:00:00-05:00
status: in-progress
confidence: vetted
tags:
  - measure
  - flow
  - genesis
  - engine
  - mermaid
  - diagram
links:
  - "[[Genesis Engine v1 recap]]"
summary: Diagram and notes describing the flow of measures through the Genesis engine.
canonical: false
---


Date: 4/14/2026


![[mermaid-diagram-genesis-measure-flow 1.png|2000]]



Mermaid Code

```
graph TB

    %% ===== ENTRY POINTS =====

    subgraph ENTRY["Entry Points"]

        CLI["CLI<br/><i>python genesis_measure.py --flags</i>"]

        UI["Tkinter UI<br/><i>python genesis_measure.py</i><br/>(no args)"]

    end

  

    %% ===== EXPERIMENT MODES =====

    subgraph MODES["Experiment Modes"]

        SINGLE["run_single_mode()<br/><i>One run, one seed</i>"]

        MULTI["run_multi_seed()<br/><i>N seeds, same params<br/>Tests SSB spontaneity</i>"]

        SWEEP["run_sweep_kappa()<br/><i>Sweep geometry coupling<br/>Finds phase transition</i>"]

        COMPARE["run_compare_geometry()<br/><i>kappa=0 vs kappa>0<br/>What geometry adds</i>"]

    end

  

    %% ===== CORE SIMULATION =====

    subgraph CORE["run_single() -- Core Simulation Loop"]

        direction TB

  

        INIT["Initialize<br/>np.random.seed(seed)<br/>state = GenesisState(N, dt)"]

  

        subgraph LOOP["Frame Loop (1 to n_frames)"]

            direction TB

  

            STEP["step(state, params, RULES, post=locking)"]

  

            subgraph ENGINE["Engine: step() in core.py"]

                direction TB

                TORQUE["torque_total = zeros(N, N)"]

  

                subgraph RULES_EXEC["Rule Pipeline"]

                    direction LR

                    R_ALIGN["alignment_rule<br/><i>sin(theta_n - theta)</i><br/>Stores: dtheta_align,<br/>grad_align in extra"]

                    R_COMP["compression_rule<br/><i>Updates tau, ux, uy</i><br/><i>Computes detF, C</i><br/><i>Shell geometry push</i><br/>Stores: detF, C in extra"]

                    R_CURV["curvature_rule<br/><i>Laplacian of ux, uy</i><br/><i>Torque toward curv dir</i>"]

                end

  

                POST["locking_postprocess<br/><i>Amplify phase/triad torques</i><br/><i>Scale by (1 - lock * C)</i>"]

                THETA_UPDATE["theta = (theta + dt * torque) % 2pi"]

  

                TORQUE --> RULES_EXEC

                R_ALIGN --> R_COMP

                R_COMP --> R_CURV

                RULES_EXEC --> POST

                POST --> THETA_UPDATE

            end

  

            subgraph MEASURE["Measurements (every log_interval frames)"]

                direction TB

                M_ORDER["|m|, angle<br/><i>compute_order_parameter()</i>"]

                M_VORTEX["vortex count<br/><i>diagnostics.detect_vortices()</i>"]

                M_HIST["theta histogram<br/><i>accumulated post-transient</i>"]

            end

  

            STEP --> ENGINE

            ENGINE --> MEASURE

        end

  

        subgraph FINAL["Final Measurements"]

            direction TB

            F_CORR["Spatial correlation C(r)<br/><i>compute_correlation()</i>"]

            F_DISP["Displacement stats<br/><i>max, mean, std of |u|</i>"]

            F_STRAIN["Strain field<br/><i>det(F), heterogeneity</i>"]

            F_COMP["Compression stats<br/><i>frac, max, mean of C</i>"]

            F_WALLS["Wall density<br/><i>neighbor disagreement > pi/4</i>"]

            F_VORTNN["Vortex NN distance<br/><i>cKDTree nearest neighbor</i>"]

        end

  

        INIT --> LOOP

        LOOP --> FINAL

    end

  

    %% ===== STATE =====

    subgraph STATE["GenesisState"]

        direction LR

        S_THETA["theta (N x N)<br/><i>orientation field</i>"]

        S_TAU["tau (N x N)<br/><i>tension</i>"]

        S_UX["ux, uy (N x N)<br/><i>displacement</i>"]

        S_C["C (N x N)<br/><i>compression</i>"]

        S_XY["X, Y (N x N)<br/><i>base grid coords</i>"]

    end

  

    %% ===== OUTPUT =====

    subgraph OUTPUT["Output (results/ directory)"]

        direction TB

        JSON["Per-run JSON<br/><i>Full data: time series,<br/>histogram, correlation,<br/>geometry metrics</i>"]

        CSV["Summary CSV<br/><i>One row per run:<br/>params, |m|, angle,<br/>vortices, geometry stats</i>"]

        CONSOLE["Console Dashboard<br/><i>Live progress, tables,<br/>ASCII phase diagrams</i>"]

    end

  

    %% ===== CONNECTIONS =====

    CLI --> MODES

    UI --> MODES

  

    SINGLE --> CORE

    MULTI -- "loop over seeds" --> CORE

    SWEEP -- "loop over kappa values" --> CORE

    COMPARE -- "loop: kappa=0 then kappa>0<br/>same seed both" --> CORE

  

    ENGINE -. "reads & mutates" .-> STATE

    MEASURE -. "reads" .-> STATE

    FINAL -. "reads" .-> STATE

  

    CORE --> JSON

    CORE --> CSV

    MODES --> CONSOLE

  

    %% ===== STYLING =====

    classDef entry fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d

    classDef modes fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e3a5f

    classDef core fill:#faf5ff,stroke:#7c3aed,stroke-width:2px,color:#3b0764

    classDef engine fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12

    classDef state fill:#f0fdfa,stroke:#0d9488,stroke-width:2px,color:#134e4a

    classDef output fill:#f8fafc,stroke:#64748b,stroke-width:1px,color:#334155

    classDef measure fill:#fefce8,stroke:#ca8a04,stroke-width:1px,color:#713f12

  

    class ENTRY entry

    class MODES modes

    class CORE core

    class ENGINE,RULES_EXEC engine

    class STATE state

    class OUTPUT output

    class MEASURE,FINAL measure
```
