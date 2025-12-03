# import numpy as np
# from genesis_scheme.engine.genesis_base_engine import Field, tension, step

# def make_unity_field(shape=(128, 128), u0=0.0):
#     F0 = np.full(shape, u0, dtype=float)
#     return Field(F0, u0=u0)

# def add_local_tension(field: Field, radius: int = 8, amplitude: float = 0.5):
#     """
#     Seed a central bump (tension) on top of unity.
#     """
#     H, W = field.shape
#     cy, cx = H // 2, W // 2

#     Y, X = np.ogrid[:H, :W]
#     mask = (X - cx)**2 + (Y - cy)**2 <= radius**2

#     F_new = field.F.copy()
#     F_new[mask] += amplitude
#     return Field(F_new, u0=field.u0)

# def main():
#     field = make_unity_field(shape=(128, 128), u0=0.0)
#     field = add_local_tension(field, radius=10, amplitude=0.7)

#     T0 = tension(field)
#     print(f"t = 0, T = {T0:.6f}")

#     alpha = 0.2  # contractive strength
#     beta  = 0.5  # expansive strength
#     gamma = 0.0  # extra nonlinear term off for now
#     dt    = 0.1  # time step (smaller = more "PDE-like")

#     for t in range(1, 301):
#         field = step(field, alpha=alpha, beta=beta, gamma=gamma, dt=dt)
#         Tt = tension(field)
#         if t % 10 == 0:
#             print(f"t = {t:4d}, T = {Tt:.6f}")

# if __name__ == "__main__":
#     main()