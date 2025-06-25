import rasterio
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import os
import matplotlib.pyplot as plt  # Add this

tiff = "C:/Users/Basel/OneDrive/Desktop/tiff/2025-06-15T00-12-00.tif"
geojson = "C:/Users/Basel/OneDrive/Desktop/tiff/2025-06-15T00-12-00.geojson"
tiff = os.path.expanduser(tiff)
tiff = tiff.replace("C:/Users/Basel/OneDrive/Desktop", "/host")
geojson = geojson.replace("C:/Users/Basel/OneDrive/Desktop", "/output")

with rasterio.open(tiff) as src:
    R, G, B = src.read(1), src.read(2), src.read(3)
    transform = src.transform
    crs = src.crs

# Apply dust mask (you can tune these thresholds)
mask = (R > 170) & (G < 113) & (B > 127)

# Optional visualization
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
rgb_img = np.stack([R, G, B], axis=-1).astype(np.uint8)
plt.imshow(rgb_img)
plt.title("Original RGB")
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(mask, cmap="Reds")
plt.title("Dust Mask")
plt.axis('off')

plt.tight_layout()
plt.show()

# Extract features from mask
results = (
    {"properties": {"value": v}, "geometry": s}
    for s, v in shapes(mask.astype(np.uint8), mask=mask, transform=transform) if v == 1
)

# Save to GeoJSON
gdf = gpd.GeoDataFrame.from_features(results, crs=crs)
gdf.to_file(geojson, driver="GeoJSON")
print(f"✅ Done: {geojson} created.")
