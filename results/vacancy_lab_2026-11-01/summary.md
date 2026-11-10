# Field Lab: vacancies and turnover

Launch from the repository root: `.\launch_sandbox.ps1`.

Open **Drop / add**, then **Flicker + Play**. Departures have pink rings; arrivals have pale flashes. Use the centered zoom and comparison controls at the top. Drop one / Add one choose a visible site. Paint also supports erase/add brushes. Stopping random switching leaves ordinary field evolution running.

Each present dash drops with probability p_out; each absent site returns with probability p_in per model update. Expected stationary occupancy is p_in/(p_out+p_in). The preset uses 0.2% out and 0.6% in: expected 75% occupancy. Missing sites have no interactions or retained state; arrivals start fresh. Geometry uses no-flux missing edges. These are experimental creative rules, isolated from the preserved engines.

The demo grew seed7 for 400 updates, then ran 600 switching updates. It ended with 3136/4096 sites present, 3843 departures and 2883 arrivals. Full-state replay was exact. Continued switching is an explicitly supplied stochastic input.

- [Preview](flicker.gif)
- [Screenshot](field_lab.png)
- [4× detail](detail.png)
- [QA](qa.json)
- [Tests](test_log.txt)
- [Manifest](manifest.json)
- [Documentation](../../docs/Genesis%20Scheme%20Vault/30-Implementation/Field%20Lab%20%E2%80%94%20Vacancies%20and%20Turnover.md)

All 71 tests pass. The research programme is shelved; this creative tool is now the active deliverable. Historical engines, theory records and evidence are retained. Classic version1 dynamics fingerprints still match.
