# pip install rasterio shapely numpy numpy
import rasterio
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape
import geopandas as gpd
import os

tiff = "~/Downloads/msg2-iodc-dust-cog/2025-06-16/2025-06-16T00-27-00.tif"
geojson = "~/Downloads/test-2025-06-16T00-27-00.geojson"
tiff = os.path.expanduser(tiff)

with rasterio.open(tiff) as src:
    R, G, B = src.read(1), src.read(2), src.read(3)
    transform = src.transform
    crs = src.crs

# Apply dust mask  هنا الفلترة (طبعا تاكدوا من هذي القيم)
mask = (R > 170) & (G < 113) & (B > 127)

results = (
    {"properties": {"value": v}, "geometry": s}
    for s, v in shapes(mask.astype(np.uint8), mask=mask, transform=transform) if v == 1
)

gdf = gpd.GeoDataFrame.from_features(results, crs=crs)
gdf.to_file(geojson, driver="GeoJSON")

print(f"✅ Done: {geojson} created.")