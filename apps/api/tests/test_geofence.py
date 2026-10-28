from apps.api.src.services.geofence_service import GeofenceService


def test_haversine_same_point():
    lat = 18.4485
    lon = 73.8245
    dist = GeofenceService.calculate_haversine_distance(lat, lon, lat, lon)
    assert dist == 0.0


def test_haversine_known_distance():
    # Distance between ZEAL Narhe Campus (18.4485, 73.8245) and Swargate Pune (18.5018, 73.8586) ~ 6.9km
    dist = GeofenceService.calculate_haversine_distance(18.4485, 73.8245, 18.5018, 73.8586)
    assert 6500 < dist < 7500


def test_geofence_inside_boundary():
    # Classroom center at ZEAL Narhe Building A
    c_lat, c_lon = 18.4485, 73.8245
    radius = 50.0  # 50m radius (+15m indoor tolerance = 65m)

    # Student sitting 20 meters away
    s_lat, s_lon = 18.4486, 73.8246
    status, dist, reason = GeofenceService.evaluate_location_evidence(
        classroom_lat=c_lat,
        classroom_lon=c_lon,
        radius_meters=radius,
        student_lat=s_lat,
        student_lon=s_lon,
        reported_accuracy_meters=15.0
    )
    assert status == "INSIDE"
    assert dist is not None
    assert dist < 65.0


def test_geofence_outside_boundary():
    c_lat, c_lon = 18.4485, 73.8245
    radius = 50.0

    # Student at home or hostel 2km away
    s_lat, s_lon = 18.4600, 73.8300
    status, dist, reason = GeofenceService.evaluate_location_evidence(
        classroom_lat=c_lat,
        classroom_lon=c_lon,
        radius_meters=radius,
        student_lat=s_lat,
        student_lon=s_lon,
        reported_accuracy_meters=10.0
    )
    assert status == "OUTSIDE"
    assert dist > 1000.0


def test_geofence_poor_accuracy():
    c_lat, c_lon = 18.4485, 73.8245
    # Even if coordinates are close, reported accuracy is 120m (exceeds 80m tolerance)
    status, dist, reason = GeofenceService.evaluate_location_evidence(
        classroom_lat=c_lat,
        classroom_lon=c_lon,
        radius_meters=50.0,
        student_lat=18.4485,
        student_lon=73.8245,
        reported_accuracy_meters=120.0
    )
    assert status == "ACCURACY_POOR"


def test_geofence_permission_denied():
    status, dist, reason = GeofenceService.evaluate_location_evidence(
        classroom_lat=18.4485,
        classroom_lon=73.8245,
        radius_meters=50.0,
        student_lat=None,
        student_lon=None
    )
    assert status == "PERMISSION_DENIED"
    assert dist is None
