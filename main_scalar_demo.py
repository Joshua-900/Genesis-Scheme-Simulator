#main_scalar_demo.py

from src.genesis_scheme import UnityState, step

def run_demo(
    s0: float = 1.0,
    t0: float = 0.4,
    iterations: int = 10
) -> None:
    unity = UnityState(s=s0, t=t0)
    print(f"{'n':>3} | {'s':>12} | {'tension':>12}")
    print("-" * 34)

    for n in range(iterations):
        print(f"{n:3d} | {unity.s:12.6f} | {unity.t:12.6f}")
        unity = step(unity)

if __name__ == "__main__":
    run_demo()