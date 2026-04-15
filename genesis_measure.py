# genesis_measure.py
#
# Headless measurement script — no visualization, pure data collection.
# Runs the minimal system (alignment + geometry + curvature + locking)
# and logs all key observables to CSV.
#
# Usage:
#   python genesis_measure.py                          # single run, default params
#   python genesis_measure.py --sweep-kappa            # sweep geometry coupling
#   python genesis_measure.py --multi-seed             # same params, 20 random seeds
#   python genesis_measure.py --sweep-kappa --N 200    # sweep at N=200
#
# Output: CSV files in results/ directory

import argparse
import os
import time
import json
import numpy as np
from pathlib import Path

from src.genesis_grid import (
    GenesisState, GenesisParams, step,
    rules_alignment, rules_compression, rules_curvature,
    rules_locking, diagnostics,
)
from src.genesis_grid.backend import to_cpu

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

RULES = [
    rules_alignment.alignment_rule,
    rules_compression.compression_rule,
    rules_curvature.curvature_rule,
]

HIST_BINS = 36
HIST_RANGE = (0, 2 * np.pi)


def make_params(alpha=0.3, gamma=0.01, kappa=0.05, curv=0.04,
                lock=0.96, shell_geom=0.08):
    """Create a GenesisParams with the minimal-system settings."""
    p = GenesisParams()
    p.alpha = alpha
    p.gamma = gamma
    p.kappa = kappa
    p.curv = curv
    p.phase = 0.0
    p.dipole = 0.0
    p.triads = 0.0
    p.lock_strength = lock
    p.phase_lock_gain = 0.0
    p.tri_lock_gain = 0.0
    p.shell_geom_gain = shell_geom
    return p


def compute_order_parameter(theta):
    """Compute |m| — magnitude of the global order parameter."""
    mean_cos = np.mean(np.cos(theta))
    mean_sin = np.mean(np.sin(theta))
    mag = np.sqrt(mean_cos**2 + mean_sin**2)
    angle = np.arctan2(mean_sin, mean_cos) % (2 * np.pi)
    return mag, angle


def compute_correlation(theta, max_r=None):
    """
    Spatial correlation function C(r) = <cos(theta(x) - theta(x+r))>
    averaged over all directions and positions.
    """
    N = theta.shape[0]
    if max_r is None:
        max_r = N // 4

    corr = np.zeros(max_r)
    for r in range(1, max_r):
        # Average over 4 directions
        c = 0.0
        c += np.mean(np.cos(theta - np.roll(theta, r, axis=0)))
        c += np.mean(np.cos(theta - np.roll(theta, -r, axis=0)))
        c += np.mean(np.cos(theta - np.roll(theta, r, axis=1)))
        c += np.mean(np.cos(theta - np.roll(theta, -r, axis=1)))
        corr[r] = c / 4.0

    corr[0] = 1.0  # self-correlation
    return corr


def run_single(N, params, n_frames, seed=None, label="run",
               log_interval=100, transient=500):
    """
    Run a single simulation and return all measurements.
    """
    if seed is not None:
        np.random.seed(seed)

    state = GenesisState(N, dt=0.05)

    # Time series storage
    ts_frame = []
    ts_mag = []
    ts_angle = []
    ts_vortices = []
    ts_time = []

    # Histogram accumulator (post-transient)
    hist_accum = np.zeros(HIST_BINS, dtype=np.float64)
    hist_count = 0

    t_start = time.perf_counter()

    for frame in range(1, n_frames + 1):
        step(state, params, RULES, post=rules_locking.locking_postprocess)

        if frame % log_interval == 0:
            theta_cpu = to_cpu(state.theta)

            mag, angle = compute_order_parameter(theta_cpu)
            vp, vm, _ = diagnostics.detect_vortices(state)
            n_vortices = len(vp) + len(vm)

            ts_frame.append(frame)
            ts_mag.append(mag)
            ts_angle.append(angle)
            ts_vortices.append(n_vortices)
            ts_time.append(time.perf_counter() - t_start)

            # Accumulate histogram post-transient
            if frame >= transient:
                counts, _ = np.histogram(theta_cpu.ravel(), bins=HIST_BINS, range=HIST_RANGE)
                hist_accum += counts.astype(np.float64)
                hist_count += 1

            if frame % (log_interval * 10) == 0:
                elapsed = time.perf_counter() - t_start
                fps = frame / elapsed
                print(f"  [{label}] frame {frame}/{n_frames}  |m|={mag:.3f}  "
                      f"angle={angle:.2f}  vortices={n_vortices}  "
                      f"({fps:.0f} fps)")

    # Final measurements
    theta_cpu = to_cpu(state.theta)
    ux_cpu = to_cpu(state.ux)
    uy_cpu = to_cpu(state.uy)
    C_cpu = to_cpu(state.C)

    final_mag, final_angle = compute_order_parameter(theta_cpu)
    final_vp, final_vm, _ = diagnostics.detect_vortices(state)
    final_vortices = len(final_vp) + len(final_vm)

    # Spatial correlation
    corr = compute_correlation(theta_cpu)

    # Displacement statistics
    disp_mag = np.sqrt(ux_cpu**2 + uy_cpu**2)

    # Compression / strain statistics
    ux_x = 0.5 * (np.roll(ux_cpu, -1, axis=1) - np.roll(ux_cpu, 1, axis=1))
    ux_y = 0.5 * (np.roll(ux_cpu, -1, axis=0) - np.roll(ux_cpu, 1, axis=0))
    uy_x = 0.5 * (np.roll(uy_cpu, -1, axis=1) - np.roll(uy_cpu, 1, axis=1))
    uy_y = 0.5 * (np.roll(uy_cpu, -1, axis=0) - np.roll(uy_cpu, 1, axis=0))
    detF = (1.0 + ux_x) * (1.0 + uy_y) - ux_y * uy_x

    # Geometry metrics
    comp_frac = float(np.mean(C_cpu > 0.5))          # fraction of cells in compression
    comp_max = float(C_cpu.max())                      # peak compression
    comp_mean = float(C_cpu.mean())                    # average compression
    strain_std = float(detF.std())                     # strain heterogeneity
    strain_min = float(detF.min())                     # most compressed point
    disp_std = float(disp_mag.std())                   # displacement heterogeneity

    # Domain wall density: fraction of cell pairs that disagree by > pi/4
    dtheta_h = np.abs(np.arctan2(np.sin(np.roll(theta_cpu, -1, axis=1) - theta_cpu),
                                  np.cos(np.roll(theta_cpu, -1, axis=1) - theta_cpu)))
    dtheta_v = np.abs(np.arctan2(np.sin(np.roll(theta_cpu, -1, axis=0) - theta_cpu),
                                  np.cos(np.roll(theta_cpu, -1, axis=0) - theta_cpu)))
    wall_density = float(np.mean((dtheta_h > np.pi/4) | (dtheta_v > np.pi/4)))

    # Vortex clustering: average distance between vortex pairs
    all_vortex_pos = final_vp + final_vm
    if len(all_vortex_pos) >= 2:
        vpos = np.array(all_vortex_pos)
        # Mean nearest-neighbor distance
        from scipy.spatial import cKDTree
        tree = cKDTree(vpos)
        dists, _ = tree.query(vpos, k=2)  # k=2: self + nearest
        nn_dist = float(dists[:, 1].mean())
    else:
        nn_dist = float('nan')

    # Histogram
    hist_avg = hist_accum / max(hist_count, 1)
    hist_ratio = hist_avg.max() / max(hist_avg.min(), 1)

    elapsed = time.perf_counter() - t_start

    result = {
        "label": label,
        "N": N,
        "seed": seed,
        "n_frames": n_frames,
        "elapsed_s": round(elapsed, 2),
        "params": {
            "alpha": params.alpha,
            "gamma": params.gamma,
            "kappa": params.kappa,
            "curv": params.curv,
            "lock": params.lock_strength,
        },
        "final": {
            "mag": round(final_mag, 4),
            "angle": round(final_angle, 4),
            "vortices": final_vortices,
            "disp_max": round(float(disp_mag.max()), 4),
            "disp_mean": round(float(disp_mag.mean()), 4),
            "hist_peak": round(float(hist_avg.max()), 2),
            "hist_trough": round(float(hist_avg.min()), 2),
            "hist_ratio": round(hist_ratio, 2),
            "hist_samples": hist_count,
        },
        "geometry": {
            "comp_frac": round(comp_frac, 4),
            "comp_max": round(comp_max, 4),
            "comp_mean": round(comp_mean, 4),
            "strain_std": round(strain_std, 4),
            "strain_min": round(strain_min, 4),
            "disp_max": round(float(disp_mag.max()), 4),
            "disp_mean": round(float(disp_mag.mean()), 4),
            "disp_std": round(disp_std, 4),
            "wall_density": round(wall_density, 4),
            "vortex_nn_dist": round(nn_dist, 4) if not np.isnan(nn_dist) else None,
        },
        "time_series": {
            "frame": ts_frame,
            "mag": [round(v, 4) for v in ts_mag],
            "angle": [round(v, 4) for v in ts_angle],
            "vortices": ts_vortices,
        },
        "histogram": {
            "bin_centers": [round(v, 4) for v in
                           np.linspace(0, 2*np.pi, HIST_BINS, endpoint=False) + np.pi/HIST_BINS],
            "counts_avg": [round(v, 2) for v in hist_avg],
        },
        "correlation": {
            "r": list(range(len(corr))),
            "C_r": [round(v, 4) for v in corr],
        },
    }

    return result


def save_result(result, filename):
    """Save result dict as JSON."""
    path = RESULTS_DIR / filename
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved: {path}")


def save_csv_summary(results, filename):
    """Save a summary CSV from a list of results."""
    path = RESULTS_DIR / filename
    with open(path, "w") as f:
        f.write("label,N,seed,kappa,curv,gamma,lock,frames,"
                "final_mag,final_angle,final_vortices,hist_ratio,"
                "disp_max,disp_mean,disp_std,"
                "comp_frac,comp_max,comp_mean,"
                "strain_std,strain_min,"
                "wall_density,vortex_nn_dist,"
                "elapsed_s\n")
        for r in results:
            p = r["params"]
            fin = r["final"]
            geo = r.get("geometry", {})
            f.write(f"{r['label']},{r['N']},{r['seed']},"
                    f"{p['kappa']},{p['curv']},{p['gamma']},{p['lock']},"
                    f"{r['n_frames']},"
                    f"{fin['mag']},{fin['angle']},{fin['vortices']},{fin['hist_ratio']},"
                    f"{geo.get('disp_max','')},{geo.get('disp_mean','')},{geo.get('disp_std','')},"
                    f"{geo.get('comp_frac','')},{geo.get('comp_max','')},{geo.get('comp_mean','')},"
                    f"{geo.get('strain_std','')},{geo.get('strain_min','')},"
                    f"{geo.get('wall_density','')},{geo.get('vortex_nn_dist','')},"
                    f"{r['elapsed_s']}\n")
    print(f"Saved summary: {path}")


# =====================================================
# Experiment modes
# =====================================================

def print_multi_seed_dashboard(results, total, t_start):
    """Print a live dashboard summarizing multi-seed progress."""
    elapsed = time.perf_counter() - t_start
    done = len(results)
    if done == 0:
        return

    mags = [r['final']['mag'] for r in results]
    angles = [r['final']['angle'] for r in results]
    vorts = [r['final']['vortices'] for r in results]

    eta = (elapsed / done) * (total - done) if done < total else 0

    print("\n" + "=" * 70)
    print(f"  MULTI-SEED PROGRESS: {done}/{total} complete  "
          f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")
    print("=" * 70)
    print(f"  {'Run':<6} {'Seed':<7} {'|m|':<8} {'Angle':<8} {'Vortices':<10} {'Verdict'}")
    print(f"  {'-'*6} {'-'*7} {'-'*8} {'-'*8} {'-'*10} {'-'*20}")

    for r in results:
        mag = r['final']['mag']
        angle = r['final']['angle']
        vort = r['final']['vortices']
        seed = r['seed']
        idx = results.index(r) + 1
        verdict = "ordered" if mag > 0.15 else "disordered"
        bar = '|' * int(mag * 30)
        print(f"  {idx:<6} {seed:<7} {mag:<8.3f} {angle:<8.2f} {vort:<10} {bar}")

    print(f"\n  |m|:    mean={np.mean(mags):.3f}  std={np.std(mags):.3f}  "
          f"[{np.min(mags):.3f} - {np.max(mags):.3f}]")

    if done >= 2:
        angle_std = np.std(angles)
        print(f"  Angle:  std={angle_std:.3f} rad  ", end="")
        if angle_std > 1.0:
            print(">>> STRONG SSB — angles widely scattered <<<")
        elif angle_std > 0.5:
            print(">> Likely SSB — angles vary <<")
        else:
            print("CAUTION — angles similar, possible bias")
    print("=" * 70)


def run_multi_seed(args):
    """Same parameters, multiple random seeds. Tests if SSB direction is arbitrary."""
    print(f"=== Multi-seed experiment: {args.seeds} seeds, N={args.N}, {args.frames} frames ===")
    print(f"    kappa={args.kappa}, curv={args.curv}, gamma={args.gamma}, lock={args.lock}")
    params = make_params(kappa=args.kappa, curv=args.curv, gamma=args.gamma, lock=args.lock)

    results = []
    t_start = time.perf_counter()

    for i in range(args.seeds):
        seed = 1000 + i
        print(f"\n--- Run {i+1}/{args.seeds} (seed={seed}) ---")
        r = run_single(args.N, params, args.frames, seed=seed,
                       label=f"seed_{seed}", log_interval=args.log_interval)
        results.append(r)

        # Live dashboard after each run
        print_multi_seed_dashboard(results, args.seeds, t_start)

    # Save individual results and summary
    for r in results:
        save_result(r, f"multi_seed_{r['label']}_N{args.N}.json")
    save_csv_summary(results, f"multi_seed_summary_N{args.N}.csv")

    # Final summary
    mags = [r['final']['mag'] for r in results]
    angles = [r['final']['angle'] for r in results]
    total_time = time.perf_counter() - t_start
    print(f"\n{'=' * 70}")
    print(f"  EXPERIMENT COMPLETE — {args.seeds} runs in {total_time:.1f}s")
    print(f"{'=' * 70}")
    print(f"  |m|: mean={np.mean(mags):.3f}, std={np.std(mags):.3f}, "
          f"min={np.min(mags):.3f}, max={np.max(mags):.3f}")
    angle_std = np.std(angles)
    print(f"  Angle: std={angle_std:.3f} rad")
    if angle_std > 1.0:
        print(f"  RESULT: >>> GENUINE SPONTANEOUS SYMMETRY BREAKING <<<")
        print(f"           Angles scatter widely. The system picks arbitrary directions.")
    elif angle_std > 0.5:
        print(f"  RESULT: >> LIKELY SSB — angles vary across runs <<")
    else:
        print(f"  RESULT: INCONCLUSIVE — angles too similar. Possible hidden bias.")
    print(f"{'=' * 70}")


def run_sweep_kappa(args):
    """Sweep geometry coupling to find the phase transition."""
    kappa_values = np.linspace(0.0, args.kappa_max, args.kappa_steps)
    print(f"=== Kappa sweep: {args.kappa_steps} values from 0 to {args.kappa_max}, "
          f"N={args.N}, {args.frames} frames ===")
    print(f"    curv={args.curv}, gamma={args.gamma}, lock={args.lock}")

    results = []
    t_start = time.perf_counter()

    for i, kappa in enumerate(kappa_values):
        print(f"\n--- Step {i+1}/{args.kappa_steps}: kappa={kappa:.4f} ---")
        params = make_params(kappa=kappa, curv=args.curv, gamma=args.gamma, lock=args.lock)
        r = run_single(args.N, params, args.frames, seed=args.seed,
                       label=f"kappa_{kappa:.4f}", log_interval=args.log_interval)
        results.append(r)

        # Live phase diagram after each step
        elapsed = time.perf_counter() - t_start
        done = len(results)
        eta = (elapsed / done) * (len(kappa_values) - done) if done < len(kappa_values) else 0

        print(f"\n{'=' * 70}")
        print(f"  KAPPA SWEEP PROGRESS: {done}/{len(kappa_values)}  "
              f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")
        print(f"{'=' * 70}")
        print(f"  {'kappa':<10} {'|m|':<8} {'Vortices':<10} {'Ratio':<8} Phase diagram")
        print(f"  {'-'*10} {'-'*8} {'-'*10} {'-'*8} {'-'*30}")

        for kv, rv in zip(kappa_values[:done], results):
            mag = rv['final']['mag']
            bar = '#' * int(mag * 40)
            marker = " <-- transition?" if done > 1 and abs(mag - 0.15) < 0.05 else ""
            print(f"  {kv:<10.4f} {mag:<8.3f} {rv['final']['vortices']:<10} "
                  f"{rv['final']['hist_ratio']:<8.2f} {bar}{marker}")
        print(f"{'=' * 70}")

    for r in results:
        save_result(r, f"sweep_kappa_{r['label']}_N{args.N}.json")
    save_csv_summary(results, f"sweep_kappa_summary_N{args.N}.csv")

    # Final phase diagram
    total_time = time.perf_counter() - t_start
    print(f"\n{'=' * 70}")
    print(f"  KAPPA SWEEP COMPLETE — {len(kappa_values)} steps in {total_time:.1f}s")
    print(f"{'=' * 70}")
    print(f"  {'kappa':<10} {'|m|':<8} Phase diagram")
    print(f"  {'-'*10} {'-'*8} {'-'*40}")
    for kv, rv in zip(kappa_values, results):
        mag = rv['final']['mag']
        bar = '#' * int(mag * 40)
        print(f"  {kv:<10.4f} {mag:<8.3f} {bar}")

    # Find approximate critical kappa
    mags = np.array([r['final']['mag'] for r in results])
    max_jump_idx = np.argmax(np.diff(mags))
    kappa_c = (kappa_values[max_jump_idx] + kappa_values[max_jump_idx + 1]) / 2
    print(f"\n  Approximate critical kappa: {kappa_c:.4f}")
    print(f"  (largest |m| jump between kappa={kappa_values[max_jump_idx]:.4f} "
          f"and kappa={kappa_values[max_jump_idx+1]:.4f})")
    print(f"{'=' * 70}")


def run_compare_geometry(args):
    """Compare kappa=0 vs kappa>0 across multiple seeds.
    Tests what geometry ADDS beyond alignment alone."""
    n_seeds = args.seeds
    print(f"{'=' * 70}")
    print(f"  GEOMETRY COMPARISON: kappa=0 vs kappa={args.kappa}")
    print(f"  N={args.N}, {args.frames} frames, {n_seeds} seeds each")
    print(f"{'=' * 70}")

    results_flat = []   # kappa=0 (alignment only, no geometry)
    results_geom = []   # kappa>0 (with geometry)

    t_start = time.perf_counter()

    for i in range(n_seeds):
        seed = 1000 + i

        # Run with kappa=0 (flat protospace)
        print(f"\n--- Seed {seed}: kappa=0 (flat) ---")
        p_flat = make_params(kappa=0.0, curv=0.0, gamma=0.0, lock=0.0)
        r_flat = run_single(args.N, p_flat, args.frames, seed=seed,
                            label=f"flat_seed_{seed}", log_interval=args.log_interval)
        results_flat.append(r_flat)

        # Run with kappa>0 (dynamic geometry) — same seed
        print(f"\n--- Seed {seed}: kappa={args.kappa} (geometry) ---")
        p_geom = make_params(kappa=args.kappa, curv=args.curv, gamma=args.gamma, lock=args.lock)
        r_geom = run_single(args.N, p_geom, args.frames, seed=seed,
                            label=f"geom_seed_{seed}", log_interval=args.log_interval)
        results_geom.append(r_geom)

        # Live comparison dashboard
        done = i + 1
        elapsed = time.perf_counter() - t_start
        eta = (elapsed / done) * (n_seeds - done) if done < n_seeds else 0

        print(f"\n{'=' * 80}")
        print(f"  GEOMETRY COMPARISON: {done}/{n_seeds} seeds  "
              f"({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")
        print(f"{'=' * 80}")
        print(f"  {'Metric':<22} {'kappa=0 (flat)':<20} {'kappa={:.3f} (geom)':<20} {'Difference':<15}".format(args.kappa))
        print(f"  {'-'*22} {'-'*20} {'-'*20} {'-'*15}")

        def avg_metric(results, key_path):
            vals = []
            for r in results:
                obj = r
                for k in key_path:
                    obj = obj.get(k, {}) if isinstance(obj, dict) else None
                    if obj is None:
                        break
                if obj is not None and not (isinstance(obj, float) and np.isnan(obj)):
                    vals.append(float(obj))
            return np.mean(vals) if vals else float('nan')

        metrics = [
            ("|m| (order)",         ["final", "mag"]),
            ("Vortices",            ["final", "vortices"]),
            ("Displacement max",    ["geometry", "disp_max"]),
            ("Displacement mean",   ["geometry", "disp_mean"]),
            ("Displacement std",    ["geometry", "disp_std"]),
            ("Compression frac",    ["geometry", "comp_frac"]),
            ("Compression max",     ["geometry", "comp_max"]),
            ("Compression mean",    ["geometry", "comp_mean"]),
            ("Strain heterogeneity",["geometry", "strain_std"]),
            ("Wall density",        ["geometry", "wall_density"]),
            ("Vortex NN distance",  ["geometry", "vortex_nn_dist"]),
        ]

        for name, path in metrics:
            v_flat = avg_metric(results_flat, path)
            v_geom = avg_metric(results_geom, path)
            if not np.isnan(v_flat) and not np.isnan(v_geom) and v_flat != 0:
                diff = f"{(v_geom - v_flat) / abs(v_flat) * 100:+.1f}%"
            elif not np.isnan(v_geom):
                diff = f"{v_geom:.4f}"
            else:
                diff = "n/a"
            print(f"  {name:<22} {v_flat:<20.4f} {v_geom:<20.4f} {diff}")

        print(f"{'=' * 80}")

    # Save everything
    all_results = results_flat + results_geom
    for r in all_results:
        save_result(r, f"compare_geom_{r['label']}_N{args.N}.json")
    save_csv_summary(all_results, f"compare_geom_summary_N{args.N}.csv")

    # Final report
    total_time = time.perf_counter() - t_start
    print(f"\n{'=' * 80}")
    print(f"  GEOMETRY COMPARISON COMPLETE — {n_seeds} seeds x 2 runs in {total_time:.1f}s")
    print(f"{'=' * 80}")

    def avg_metric(results, key_path):
        vals = []
        for r in results:
            obj = r
            for k in key_path:
                obj = obj.get(k, {}) if isinstance(obj, dict) else None
                if obj is None:
                    break
            if obj is not None and not (isinstance(obj, float) and np.isnan(obj)):
                vals.append(float(obj))
        return np.mean(vals) if vals else float('nan')

    print(f"\n  What geometry adds (kappa=0 -> kappa={args.kappa}):")
    key_metrics = [
        ("Displacement mean",   ["geometry", "disp_mean"],  "protospace deformation"),
        ("Compression frac",    ["geometry", "comp_frac"],  "fraction of folded cells"),
        ("Strain heterogeneity",["geometry", "strain_std"], "geometric structure variation"),
        ("Wall density",        ["geometry", "wall_density"], "domain boundary sharpness"),
        ("Vortex NN distance",  ["geometry", "vortex_nn_dist"], "defect spatial organization"),
    ]

    for name, path, meaning in key_metrics:
        v_flat = avg_metric(results_flat, path)
        v_geom = avg_metric(results_geom, path)
        if not np.isnan(v_flat) and not np.isnan(v_geom):
            if v_flat > 0:
                ratio = v_geom / v_flat
                print(f"  {name:<22} {v_flat:.4f} -> {v_geom:.4f}  ({ratio:.1f}x)  — {meaning}")
            else:
                print(f"  {name:<22} {v_flat:.4f} -> {v_geom:.4f}  — {meaning}")
        else:
            print(f"  {name:<22} n/a")

    print(f"{'=' * 80}")


def run_single_mode(args):
    """Single run with specified parameters."""
    print(f"=== Single run: N={args.N}, {args.frames} frames, seed={args.seed} ===")
    params = make_params(kappa=args.kappa, curv=args.curv, gamma=args.gamma, lock=args.lock)
    r = run_single(args.N, params, args.frames, seed=args.seed,
                   label="single", log_interval=args.log_interval)

    save_result(r, f"single_N{args.N}_seed{args.seed}.json")

    print(f"\n=== Final State ===")
    print(f"|m| = {r['final']['mag']:.4f}")
    print(f"Angle = {r['final']['angle']:.4f} rad")
    print(f"Vortices = {r['final']['vortices']}")
    print(f"Hist ratio = {r['final']['hist_ratio']:.2f}")
    print(f"Displacement max = {r['final']['disp_max']:.4f}")
    print(f"Elapsed = {r['elapsed_s']:.1f}s")


# =====================================================
# Interactive UI for parameter input
# =====================================================

def run_ui():
    """Launch a tkinter form to configure and run experiments."""
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("GenesisScheme — Measurement Setup")
    root.configure(bg="#1e1e2e")
    root.resizable(False, False)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
    style.configure("Header.TLabel", background="#1e1e2e", foreground="#89b4fa", font=("Segoe UI", 12, "bold"))
    style.configure("Section.TLabel", background="#1e1e2e", foreground="#a6adc8", font=("Segoe UI", 9, "bold"))
    style.configure("TEntry", fieldbackground="#313244", foreground="#cdd6f4")
    style.configure("TButton", font=("Segoe UI", 10, "bold"))
    style.configure("Run.TButton", background="#a6e3a1", foreground="#1e1e2e")
    style.configure("TRadiobutton", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
    style.configure("TFrame", background="#1e1e2e")

    # Header
    ttk.Label(root, text="GenesisScheme Measurement", style="Header.TLabel").grid(
        row=0, column=0, columnspan=4, pady=(15, 5), padx=20)
    ttk.Label(root, text="Configure experiment parameters, then click Run.", style="TLabel").grid(
        row=1, column=0, columnspan=4, pady=(0, 10), padx=20)

    # --- Experiment mode ---
    mode_frame = ttk.Frame(root)
    mode_frame.grid(row=2, column=0, columnspan=4, pady=5, padx=20, sticky="w")
    ttk.Label(mode_frame, text="EXPERIMENT MODE", style="Section.TLabel").pack(anchor="w")

    mode_var = tk.StringVar(value="single")
    modes = [("Single Run", "single"), ("Multi-Seed (SSB proof)", "multi_seed"),
             ("Kappa Sweep (phase transition)", "sweep_kappa"),
             ("Compare Geometry (what geometry adds)", "compare_geometry")]
    for text, val in modes:
        ttk.Radiobutton(mode_frame, text=text, variable=mode_var, value=val).pack(anchor="w", padx=10)

    # --- Parameter entries ---
    def make_param_row(parent, row, label, default, tooltip=""):
        ttk.Label(parent, text=label, style="TLabel").grid(row=row, column=0, sticky="e", padx=(20, 5), pady=3)
        var = tk.StringVar(value=str(default))
        entry = ttk.Entry(parent, textvariable=var, width=12)
        entry.grid(row=row, column=1, sticky="w", padx=5, pady=3)
        if tooltip:
            ttk.Label(parent, text=tooltip, style="TLabel", foreground="#585b70").grid(
                row=row, column=2, columnspan=2, sticky="w", padx=5)
        return var

    ttk.Label(root, text="GRID & SIMULATION", style="Section.TLabel").grid(
        row=10, column=0, columnspan=4, pady=(15, 2), padx=20, sticky="w")

    v_N      = make_param_row(root, 11, "N (grid size)", 200, "50-500")
    v_frames = make_param_row(root, 12, "Frames", 10000, "steps to simulate")
    v_seed   = make_param_row(root, 13, "Seed", 42, "random seed (single run)")
    v_log    = make_param_row(root, 14, "Log interval", 100, "measure every N frames")

    ttk.Label(root, text="PHYSICS PARAMETERS", style="Section.TLabel").grid(
        row=20, column=0, columnspan=4, pady=(15, 2), padx=20, sticky="w")

    v_alpha = make_param_row(root, 21, "Align (alpha)", 0.3)
    v_gamma = make_param_row(root, 22, "Tension (gamma)", 0.01)
    v_kappa = make_param_row(root, 23, "Geometry (kappa)", 0.097, "key parameter for SSB")
    v_curv  = make_param_row(root, 24, "Curvature", 0.04)
    v_lock  = make_param_row(root, 25, "Lock strength", 0.96)

    ttk.Label(root, text="EXPERIMENT-SPECIFIC", style="Section.TLabel").grid(
        row=30, column=0, columnspan=4, pady=(15, 2), padx=20, sticky="w")

    v_seeds      = make_param_row(root, 31, "Seeds (multi-seed)", 20, "number of runs")
    v_kappa_max  = make_param_row(root, 32, "Kappa max (sweep)", 0.1)
    v_kappa_steps = make_param_row(root, 33, "Kappa steps (sweep)", 20)

    # --- Status label ---
    status_var = tk.StringVar(value="Ready")
    status_label = ttk.Label(root, textvariable=status_var, style="TLabel", foreground="#f9e2af")
    status_label.grid(row=40, column=0, columnspan=4, pady=(15, 5), padx=20)

    # --- Run button ---
    def on_run():
        # Build an args-like object from the form values
        class Args:
            pass

        args = Args()
        try:
            args.N = int(v_N.get())
            args.frames = int(v_frames.get())
            args.seed = int(v_seed.get())
            args.log_interval = int(v_log.get())
            args.alpha = float(v_alpha.get())
            args.gamma = float(v_gamma.get())
            args.kappa = float(v_kappa.get())
            args.curv = float(v_curv.get())
            args.lock = float(v_lock.get())
            args.seeds = int(v_seeds.get())
            args.kappa_max = float(v_kappa_max.get())
            args.kappa_steps = int(v_kappa_steps.get())
        except ValueError as e:
            status_var.set(f"Invalid input: {e}")
            return

        mode = mode_var.get()
        status_var.set(f"Running {mode}... (see console for progress)")
        root.update()

        # Close the UI window and run
        root.destroy()

        if mode == "multi_seed":
            run_multi_seed(args)
        elif mode == "sweep_kappa":
            run_sweep_kappa(args)
        elif mode == "compare_geometry":
            run_compare_geometry(args)
        else:
            run_single_mode(args)

    btn_frame = ttk.Frame(root)
    btn_frame.grid(row=41, column=0, columnspan=4, pady=(5, 20))
    run_btn = tk.Button(btn_frame, text="  Run Experiment  ", font=("Segoe UI", 11, "bold"),
                        bg="#a6e3a1", fg="#1e1e2e", activebackground="#94e2d5",
                        relief="flat", padx=20, pady=8, command=on_run)
    run_btn.pack()

    root.mainloop()


# =====================================================
# CLI
# =====================================================

def main():
    parser = argparse.ArgumentParser(description="GenesisScheme headless measurement")
    parser.add_argument("--N", type=int, default=100, help="Grid size (default: 100)")
    parser.add_argument("--frames", type=int, default=10000, help="Frames to run (default: 10000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--log-interval", type=int, default=100, help="Log every N frames")

    # Parameters
    parser.add_argument("--kappa", type=float, default=0.097, help="Geometry coupling")
    parser.add_argument("--curv", type=float, default=0.04, help="Curvature feedback")
    parser.add_argument("--gamma", type=float, default=0.01, help="Tension gain")
    parser.add_argument("--lock", type=float, default=0.96, help="Lock strength")
    parser.add_argument("--alpha", type=float, default=0.3, help="Alignment coupling")

    # Experiment modes
    parser.add_argument("--multi-seed", action="store_true", help="Run multiple random seeds")
    parser.add_argument("--seeds", type=int, default=20, help="Number of seeds for multi-seed")

    parser.add_argument("--sweep-kappa", action="store_true", help="Sweep geometry coupling")
    parser.add_argument("--kappa-max", type=float, default=0.1, help="Max kappa for sweep")
    parser.add_argument("--kappa-steps", type=int, default=20, help="Steps in kappa sweep")

    parser.add_argument("--compare-geometry", action="store_true",
                        help="Compare kappa=0 vs kappa>0: what does geometry add?")

    parser.add_argument("--no-ui", action="store_true", help="Skip UI, use CLI args only")

    args = parser.parse_args()

    # If no experiment flags and no --no-ui, show the UI
    if not args.no_ui and not args.multi_seed and not args.sweep_kappa and not args.compare_geometry:
        # Check if any non-default args were passed (indicates CLI usage)
        import sys
        if len(sys.argv) <= 1:
            run_ui()
            return

    if args.compare_geometry:
        run_compare_geometry(args)
    elif args.multi_seed:
        run_multi_seed(args)
    elif args.sweep_kappa:
        run_sweep_kappa(args)
    else:
        run_single_mode(args)


if __name__ == "__main__":
    main()
