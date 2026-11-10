# Live formula editor

A modeless editor accepts scalar guidance and two-formula vector currents.
It includes draft previews, response modes, examples, spatial scale, model-time
speed and target strength. Apply is explicit. Draft previews and failed applies
do not change the model. Unsupported Python constructs are rejected by an AST
interpreter; no eval or compilation is used.

Formula state is saved in version-two bundles. Version-one bundles still load.
Runtime singularities pause playback/Step before the failing tick; RNG and
transition progress are preserved. Static fields are cached. Arbitrary formulas
can have discontinuities at the periodic domain seams.

104 tests pass, including 13 formula-specific contracts. Native Windows/GPU QA
checked scalar and vector apply, preview isolation, rejection of Python access,
and exact continued evolution from a saved formula state. See `qa.json` and
`verify_native.py`. Editor screenshots show actual native UI, and the field
image shows the radial formula influencing the live agents.

Use `.\launch_physarum.ps1` and click Formula editor. Full language and
coordinate conventions are documented in `src/physarum_lab/README.md`.
