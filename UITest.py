import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import rasterio
import cv2
from rasterio.features import shapes
import geopandas as gpd

def select_file():
    path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif")])
    if not path:
        return
    process_tiff(path)

def process_tiff(tiff_path):
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

        results = (
            {"properties": {"value": v}, "geometry": s}
            for s, v in shapes(binary_mask, mask=binary_mask, transform=transform)
            if v == 1
        )

        gdf = gpd.GeoDataFrame.from_features(results, crs=crs).to_crs("EPSG:4326")
        geojson_path = tiff_path.replace('.tif', '_dust.geojson')
        gdf.to_file(geojson_path, driver='GeoJSON')

        messagebox.showinfo("Success", f"GeoJSON saved:\n{geojson_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Tkinter UI
root = tk.Tk()
root.title("Dust Detection Tool")

tk.Label(root, text="Click to select a TIFF image:").pack(pady=10)
tk.Button(root, text="Browse...", command=select_file).pack(pady=5)

root.mainloop()
