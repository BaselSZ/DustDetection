import streamlit as st
import numpy as np
import rasterio
import cv2
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
from io import BytesIO

st.title("Dust Detection from Satellite TIFF")

uploaded_file = st.file_uploader("Upload a .tif image", type=["tif"])

if uploaded_file:
    with rasterio.open(BytesIO(uploaded_file.read())) as src:
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
    geojson_bytes = gdf.to_json().encode("utf-8")

    st.success("Dust detected and converted to GeoJSON.")
    st.download_button("Download GeoJSON", geojson_bytes, file_name="dust.geojson", mime="application/geo+json")
