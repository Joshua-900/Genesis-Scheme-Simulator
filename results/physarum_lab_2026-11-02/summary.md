# Physarum Studio — first working version

An independent artificial-life art simulator with modular numerical domain,
application policy, graphics, desktop controls and storage. Existing Genesis
implementations and source fingerprints remain intact.

Launch `.\launch_physarum.ps1`. Desktop defaults to 512 square / 90,000 agents.
Fine runs: `.venv\Scripts\python.exe -B -m src.physarum_lab --size 640
--agents 150000`. The recorded behavior demo uses this fine configuration.

Silk, Estuary and Filigree offer different motion. Current strength varies an
authored curl field. Gather/Release ramps a wave-based nodal attraction over
100 ticks and quiets the current. Formula symmetries are externally supplied;
the agents' detailed trajectories and trails develop through their interactions.
This is not a physical fluid solver or proof of a Genesis claim.

Exports include full-field 1600px artwork, numerical arrays, rules, RNG state,
transition progress and source fingerprints. Loading is paused. Snapshots are
validated, checksummed, and never unpickled. The source/numerical environment
must remain compatible for exact future evolution.

91 automated tests cover numerical accounting, reproducibility, continuation,
guidance and desktop interactions, including the preserved prior suites. Native
Windows GPU QA compares framebuffer pixels with the headless renderer and
checks controls. See qa.json for actual measured performance; it depends on
population, field resolution and graphics hardware. Simulation is CPU-based;
GPU rendering and software fallback are both available.

`behavior.gif` is actual evolving simulation, sampled every 16 ticks and
played back faster than its computation. It shows flow, gathering, and release.
`flow.png`, `gather.png` and `release.png` are their full-field images; companion
`*_state` directories contain resumable states. The flow/gather/release mean
squared wave amplitudes at agents are approximately .122, .011 and .066.
This metric measures closeness to the designed nodal lines in this run, not
biological fitness or general emergence.

The current artistic direction is a first implementation for user judgment.
Native imagery, parameter controls and test results are concrete; beauty and
long-term novelty are not guaranteed by the implementation.
