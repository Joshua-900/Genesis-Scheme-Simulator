---
Area: Implementation
datetime_stamp: 2026-04-14T00:00:00-05:00
status: complete
confidence: tentative
tags:
  - mermaid
  - diagram
  - rule
  - pipeline
  - engine
links:
  - "[[Genesis Engine v1 recap]]"
summary: Diagram of the rule pipeline used by the Genesis engine.
canonical: false
---


Date: 4/14/2026

![[mermaid-diagram-genesis-rule-pipeline.png]]

Mermaid Code

```
flowchart TD

    A["Frame start"] --> B["Read sliders / set params"]

    B --> C["step(state, params, RULES, post=locking)"]

  

    subgraph STEP["Engine step()"]

        C --> S0["torque_total = 0; extra = {}"]

  

        S0 --> R1["Alignment rule"]

        R1 --> R1a["compute dtheta_align"]

        R1a --> R1b["extra.grad_align = abs(dtheta_align)"]

        R1b --> R1c["torque += alpha * dtheta_align"]

  

        R1c --> R2["Compression rule"]

        R2 --> R2a["tau update from grad_align"]

        R2a --> R2b["ux, uy update from tau and theta"]

        R2b --> R2c["detF from ux, uy gradients"]

        R2c --> R2d["C = exp(-(detF^2)/sigma_c2)"]

        R2d --> R2e["extra.C = C; torque += 0.1 * tau"]

  

        R2e --> R3["Curvature rule"]

        R3 --> R3a["laplacian(ux), laplacian(uy)"]

        R3a --> R3b["phi_curv, curv_mag"]

        R3b --> R3c["torque += curv * curv_mag * sin(phi_curv - theta)"]

  

        R3c --> P{"postprocess?"}

        P -->|yes| L["locking: torque *= (1 - lock_strength * C)"]

        P -->|no| U["skip"]

        L --> T["theta = (theta + dt * torque) mod 2pi"]

        U --> T

    end

  

    T --> D["to_cpu(theta, ux, uy, C)"]

    D --> E["diagnostics: vortices, unity, hist, |m|"]

    E --> F["render: dashes, compression bg, contours, mesh"]

    F --> A
```
