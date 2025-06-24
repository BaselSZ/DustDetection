import cv2
import numpy as np
import matplotlib.pyplot as plt
import rasterio
import json
from shapely.geometry import mapping, Polygon
from rasterio.features import shapes
from rasterio.transform import from_origin

tiff_path = "C:/Users/Basel/OneDrive/Desktop/msg2-iodc-dust-cog/msg2-iodc-dust-cog/2025-06-15/2025-06-15T00-12-00.tif"
with rasterio.open(tiff_path) as src:
    image = src.read([1, 2, 3])  
    transform = src.transform
    crs = src.crs

# Convert to HWC format (Height x Width x Channels)
image = np.transpose(image, (1, 2, 0))
image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

# Detect pink to violet colors
lower_color = np.array([140, 50, 100])
upper_color = np.array([170, 255, 255])
dust_mask = cv2.inRange(hsv, lower_color, upper_color)

kernel = np.ones((5, 5), np.uint8)
dust_mask_clean = cv2.morphologyEx(dust_mask, cv2.MORPH_OPEN, kernel)
dust_mask_clean = cv2.morphologyEx(dust_mask_clean, cv2.MORPH_CLOSE, kernel)
results = []
for geom, val in shapes(dust_mask_clean, mask=dust_mask_clean.astype(bool), transform=transform):
    if val == 255:  # only foreground
        results.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {}
        })

geojson = {
    "type": "FeatureCollection",
    "features": results
}
# Save to file
geojson_path = tiff_path.replace(".tif", "_dust.geojson")
with open(geojson_path, "w") as f:
    json.dump(geojson, f)

plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title("original image")
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(dust_mask_clean, cmap='gray')
plt.title("Detected Dust Areas")
plt.axis('off')
plt.tight_layout()
plt.show()
print(f"✅ Done: {geojson_path} created.")