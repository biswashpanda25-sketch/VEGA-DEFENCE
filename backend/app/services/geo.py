"""Odisha district reference data — approximate centroids, public administrative geography.
Used purely for client-side visualization anchoring; not a survey-accurate boundary source.
Replace `geojson` with authoritative Survey of India / Census administrative boundaries
under licence before operational deployment.
"""
DISTRICTS = [
    ("Khordha", 20.18, 85.62), ("Cuttack", 20.46, 85.88), ("Puri", 19.81, 85.83),
    ("Ganjam", 19.38, 84.83), ("Sambalpur", 21.47, 83.97), ("Sundargarh", 22.12, 84.03),
    ("Keonjhar", 21.63, 85.58), ("Mayurbhanj", 21.93, 86.73), ("Balasore", 21.50, 86.93),
    ("Bhadrak", 21.06, 86.50), ("Jajpur", 20.85, 86.33), ("Dhenkanal", 20.67, 85.60),
    ("Angul", 20.84, 85.10), ("Bargarh", 21.33, 83.62), ("Jharsuguda", 21.86, 84.01),
    ("Bolangir", 20.70, 83.48), ("Kalahandi", 19.91, 83.17), ("Koraput", 18.81, 82.71),
    ("Rayagada", 19.17, 83.42), ("Nabarangpur", 19.23, 82.55), ("Malkangiri", 18.35, 81.88),
    ("Kandhamal", 20.30, 84.20), ("Boudh", 20.83, 84.32), ("Subarnapur", 20.85, 83.90),
    ("Nuapada", 20.82, 82.53), ("Gajapati", 18.90, 84.18), ("Nayagarh", 20.13, 85.10),
    ("Kendrapara", 20.50, 86.42), ("Jagatsinghpur", 20.27, 86.17), ("Deogarh", 21.53, 84.73),
]

def odisha_district_geojson() -> dict:
    return {
        "type": "FeatureCollection",
        "name": "odisha_districts_reference",
        "metadata": {
            "source": "Public administrative geography — approximate district centroids",
            "licence": "Reference data; replace with licensed Survey of India boundaries for production",
            "freshness": "static reference",
        },
        "features": [
            {"type": "Feature", "id": name.lower().replace(" ", "_"),
             "properties": {"district": name, "state": "Odisha", "centroid": [lon, lat]},
             "geometry": {"type": "Point", "coordinates": [lon, lat]}}
            for name, lat, lon in DISTRICTS
        ],
    }

DISTRICT_NAMES = [d[0] for d in DISTRICTS]
