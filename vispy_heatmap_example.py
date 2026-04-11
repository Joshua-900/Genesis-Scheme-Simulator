import numpy as np
from vispy import app, scene

# Example grid data (replace with your own)
N = 40
# Simulate a heatmap (compression field)
compression_field = np.random.rand(N, N)

canvas = scene.SceneCanvas(keys='interactive', show=True)
view = canvas.central_widget.add_view()

# Create an image visual (heatmap)
image = scene.visuals.Image(compression_field, cmap='gray', interpolation='bilinear', parent=view.scene)

# Optionally, add a colorbar
colorbar = scene.visuals.ColorBar(
    cmap='gray',
    orientation='right',
    size=(10, 2),
    parent=canvas.scene,
    label='Compression',
    clim=(compression_field.min(), compression_field.max())
)
# Removed manual colorbar position to avoid ValueError

view.camera = scene.PanZoomCamera(rect=(0, 0, N, N))

if __name__ == '__main__':
    app.run()
