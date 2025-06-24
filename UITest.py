import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import rasterio
import cv2
from rasterio.features import shapes
import geopandas as gpd

# Setup main app window
root = tk.Tk()
root.title("Dust Detection App")

# Create frame for matplotlib output
plot_frame = tk.Frame(root)
plot_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

canvas = None  # Will hold the matplotlib canvas

def select_file():
    path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif")])
    if not path:
        return
    process_tiff(path)

def process_tiff(tiff_path):
    global canvas
    try:
        with rasterio.open(tiff_path) as src:
            rgb = src.read([1, 2, 3])
            transform = src.transform
            crs = src.crs

        img = np.transpose(rgb, (1, 2, 0)).astype(np.uint8)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        lower_hsv = np.array([140, 40, 40])
        upper_hsv = np.array([170, 255, 255])
        mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
        binary_mask = (mask > 0).astype(np.uint8)

        # Save GeoJSON
        results = (
            {"properties": {"value": v}, "geometry": s}
            for s, v in shapes(binary_mask, mask=binary_mask, transform=transform)
            if v == 1
        )
        gdf = gpd.GeoDataFrame.from_features(results, crs=crs).to_crs("EPSG:4326")
        geojson_path = tiff_path.replace('.tif', '_dust.geojson')
        gdf.to_file(geojson_path, driver='GeoJSON')

        # Clear old plot if exists
        if canvas:
            canvas.get_tk_widget().destroy()

        # Create new matplotlib figure
        fig, axes = plt.subplots(1, 2, figsize=(8, 4))

        axes[0].imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        axes[0].set_title("Original Image")
        axes[0].axis('off')

        axes[1].imshow(binary_mask, cmap='gray')
        axes[1].set_title("Detected Dust")
        axes[1].axis('off')

        fig.tight_layout()

        # Embed into Tkinter
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        messagebox.showinfo("Success", f"GeoJSON saved at:\n{geojson_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))


# UI Controls
tk.Label(root, text="Select a .tif image for dust detection").pack(pady=5)
tk.Button(root, text="Browse Image", command=select_file).pack(pady=5)

root.mainloop()
