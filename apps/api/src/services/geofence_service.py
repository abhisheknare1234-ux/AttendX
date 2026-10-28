import math
from typing import Tuple, Optional
from apps.api.src.core.config import settings


class GeofenceService:
    EARTH_RADIUS_METERS = 6371000.0  # WGS-84 mean radius

    @staticmethod
    def calculate_haversine_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate the great-circle distance between two points
        on the Earth's surface using the Haversine formula.
        Returns distance in meters.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return GeofenceService.EARTH_RADIUS_METERS * c

    @classmethod
    def evaluate_location_evidence(
        cls,
        classroom_lat: float,
        classroom_lon: float,
        radius_meters: float,
        student_lat: Optional[float],
        student_lon: Optional[float],
        reported_accuracy_meters: Optional[float] = None
    ) -> Tuple[str, Optional[float], str]:
        """
        Evaluates geolocation evidence against classroom anchor.
        Returns:
            - status: INSIDE, OUTSIDE, ACCURACY_POOR, PERMISSION_DENIED, UNAVAILABLE
            - distance_meters: float or None
            - reason_detail: descriptive explanation
        """
        if student_lat is None or student_lon is None:
            return "PERMISSION_DENIED", None, "Client provided no GPS coordinates (permission denied or unavailable)"

        # Coordinate range sanity check
        if not (-90.0 <= student_lat <= 90.0) or not (-180.0 <= student_lon <= 180.0):
            return "UNAVAILABLE", None, "Provided GPS coordinates are outside valid physical range"

        # Accuracy check (indoor multipath interference in college buildings)
        if reported_accuracy_meters is not None:
            if reported_accuracy_meters > settings.MAX_ALLOWED_LOCATION_ACCURACY_METERS:
                distance = cls.calculate_haversine_distance(classroom_lat, classroom_lon, student_lat, student_lon)
                return (
                    "ACCURACY_POOR",
                    round(distance, 2),
                    f"Reported location accuracy {reported_accuracy_meters:.1f}m exceeds tolerance ({settings.MAX_ALLOWED_LOCATION_ACCURACY_METERS}m)"
                )

        distance = cls.calculate_haversine_distance(classroom_lat, classroom_lon, student_lat, student_lon)
        rounded_dist = round(distance, 2)

        # Allow an indoor structure tolerance buffer (+15m) for multi-story college blocks
        effective_radius = radius_meters + 15.0

        if distance <= effective_radius:
            return "INSIDE", rounded_dist, f"Located {rounded_dist:.1f}m from classroom center (within {effective_radius:.1f}m boundary)"
        else:
            return "OUTSIDE", rounded_dist, f"Located {rounded_dist:.1f}m from classroom center (exceeds {effective_radius:.1f}m boundary)"
