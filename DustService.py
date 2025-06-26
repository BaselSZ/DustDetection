import cv2
import numpy as np
import matplotlib.pyplot as plt
import rasterio
import json
import geopandas as gpd
from shapely.geometry import mapping, Polygon
from rasterio.features import shapes
from rasterio.transform import from_origin
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
import os
#Crop a specific area from a TIFF file and detect dust areas in it
print("Files in /app/data:")
print(os.listdir("/app/data"))
tiff = "/app/data/2025-06-15T00-12-00.tif"
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
    #saving the cropped image
tiff = tiff.replace(".tif", "_cropped.tif")
with rasterio.open(tiff, "w", **profile) as dst:
    dst.write(data)
    print(f"✅ Created cropped image at: {tiff}")

#get the dust areas from the cropped TIFF file
tiff_path = "/app/data/2025-06-15T00-12-00_cropped.tif"
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

binary_mask = (dust_mask > 0).astype(np.uint8)

# Extract polygon shapes from the binary mask
results = (
    {"properties": {"value": v}, "geometry": s}
    for s, v in shapes(binary_mask, mask=binary_mask, transform=transform)
    if v == 1
)

# Save polygons as GeoJSON
gdf = gpd.GeoDataFrame.from_features(results, crs=crs).to_crs("EPSG:4326")
geojson_path = tiff_path.replace('.tif', '_dust.geojson').replace('.tiff', '_dust.geojson')
gdf.to_file(geojson_path, driver='GeoJSON')

plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.imshow(image)
plt.title("original image")
plt.axis('off')

plt.subplot(1, 2, 2)
plt.imshow(dust_mask, cmap='gray')
plt.title("Detected Dust Areas")
plt.axis('off')
plt.tight_layout()
plt.show()
print(f"✅ Done: {geojson_path} created.")