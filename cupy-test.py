import cupy as cp
x = cp.arange(10**7,dtype=cp.float32)
print("Device:", cp.cuda.runtime.getDevice())
print("Sum:", float(x.sum()))
