import cv2
import numpy as np
import matplotlib.pyplot as plt
import rasterio
import json
from shapely.geometry import mapping, Polygon
from rasterio.features import shapes
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
#Crop a specific area from a TIFF file and detect dust areas in it
tiff = "C:/Users/Basel/OneDrive/Desktop/msg2-iodc-dust-cog/msg2-iodc-dust-cog/2025-06-15/2025-06-15T00-12-00.tif"
# KSA bounding box in EPSG:3857 (Web Mercator)
ksa_bounds = [3540000, 1560000, 6330000, 4090000]

with rasterio.open(tiff) as src:
    bounds = transform_bounds("EPSG:3857", src.crs, *ksa_bounds)
    window = from_bounds(*bounds, src.transform)
    data = src.read(window=window)
    profile = src.profile
    profile.update({
        "height": data.shape[1],
        "width": data.shape[2],
        "transform": src.window_transform(window)
    })
with rasterio.open("C:/Users/Basel/OneDrive/Desktop/msg2-iodc-dust-cog/msg2-iodc-dust-cog/2025-06-15/2025-06-15T00-12-00_cropped.tif", "w", **profile) as dst:
    dst.write(data)
    print(f"✅ Created cropped image at: {tiff}")
    
#get the dust areas from the cropped TIFF file
tiff_path = "C:/Users/Basel/OneDrive/Desktop/msg2-iodc-dust-cog/msg2-iodc-dust-cog/2025-06-15/2025-06-15T00-12-00_cropped.tif"
with rasterio.open(tiff_path) as src:
    image = src.read([1, 2, 3])  
    transform = src.transform
    crs = src.crs

# Convert to HWC format (Height x Width x Channels)
image = np.transpose(image, (1, 2, 0))
image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

# Detect pink to violet colors
lower_color = np.array([140, 40, 40])
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