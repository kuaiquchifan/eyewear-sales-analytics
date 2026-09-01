import random
import math
from data_sheet_create_0_1 import StoreInfo, session

random.seed(43)

CITY_CENTERS = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698),
    "Miami": (25.7617, -80.1918),
    "Seattle": (47.6062, -122.3321),
    "Boston": (42.3601, -71.0589),
    "San Francisco": (37.7749, -122.4194),
    "Dallas": (32.7767, -96.7970),
    "Atlanta": (33.7490, -84.3880),
    "Philadelphia": (39.9526, -75.1652),
    "Washington": (38.9072, -77.0369),
    "Denver": (39.7392, -104.9903),
    "Phoenix": (33.4484, -112.0740),
    "Las Vegas": (36.1699, -115.1398),
}

def simulate_location(city: str, region: str, country: str):
    city = (city or "").strip()
    region = (region or "").strip()
    country = (country or "").strip()

    center = CITY_CENTERS.get(city)
    if center is None:
        region_city_map = {
            "California": (36.7783, -119.4179),
            "New York": (42.6526, -73.7562),
            "Texas": (31.9686, -99.9018),
            "Florida": (27.6648, -81.5158),
            "Illinois": (40.6331, -89.3985),
            "Washington": (47.7511, -120.7401),
            "Georgia": (32.1656, -82.9001),
            "Massachusetts": (42.4072, -71.3824),
            "Virginia": (37.4316, -78.6569),
            "Colorado": (39.5501, -105.7821),
        }
        center = region_city_map.get(region, (39.8283, -98.5795))

    lat0, lon0 = center

    radius_km = random.uniform(0.5, 10.0)
    angle = random.uniform(0, 2 * math.pi)

    lat_offset = (radius_km / 111.0) * math.cos(angle)
    lon_offset = (radius_km / (111.0 * math.cos(math.radians(lat0)))) * math.sin(angle)

    lat = lat0 + lat_offset
    lon = lon0 + lon_offset

    return round(lat, 6), round(lon, 6)


def update_store_locations():
    stores = session.query(StoreInfo).all()

    for store in stores:
        # 只补齐没有坐标的门店
        if store.latitude is None or store.longitude is None:
            lat, lon = simulate_location(
                store.store_city,
                store.store_region,
                store.store_country
            )
            store.latitude = lat
            store.longitude = lon

    session.commit()
    print(f"已更新 {len(stores)} 条门店位置。")


if __name__ == "__main__":
    update_store_locations()