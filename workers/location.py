"""Location validation and nearby-worker selection helpers."""

from math import asin, cos, radians, sin, sqrt


def distance_km(latitude_a, longitude_a, latitude_b, longitude_b):
    """Return the great-circle distance between two coordinates in kilometres."""
    latitude_a, longitude_a, latitude_b, longitude_b = map(
        float, (latitude_a, longitude_a, latitude_b, longitude_b)
    )
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(latitude_a))
        * cos(radians(latitude_b))
        * sin(longitude_delta / 2) ** 2
    )
    return 2 * 6371.0088 * asin(sqrt(haversine))


def nearby_workers(workers, customer_location):
    """Keep workers whose own work range covers the customer's location."""
    customer_latitude, customer_longitude = customer_location
    matching_workers = []
    for worker in workers:
        if worker.latitude is None or worker.longitude is None:
            continue
        worker.distance_km = round(
            distance_km(customer_latitude, customer_longitude, worker.latitude, worker.longitude), 1
        )
        if worker.distance_km <= float(worker.work_range):
            matching_workers.append(worker)
    return sorted(matching_workers, key=lambda worker: worker.distance_km)
