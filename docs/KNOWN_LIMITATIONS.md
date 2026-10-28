# ATTENDX AI — Known Limitations & Defensibility Register

Honest technical documentation of verification limitations as required by institutional engineering standards.

---

## 1. Physical Verification Factor Limitations

### 1.1 GPS Geofencing Indoors
- **Multipath Interference & Attenuation**: In reinforced concrete buildings (such as ZEAL Building A or B), satellite line-of-sight is obstructed. Reported mobile accuracy may degrade from 5m to 40–90m.
- **Defensibility Response**: AttendX AI incorporates a configurable accuracy threshold (`settings.MAX_ALLOWED_LOCATION_ACCURACY_METERS = 80.0`) and routes uncertain cases to the Teacher Review Queue rather than issuing false accusations of cheating.
- **Client OS Mock Locations**: Browsers query the operating system's location service. Rooted or modified devices can supply synthetic coordinates. For this reason, GPS is never the sole factor; it is combined with dynamic line-of-sight QR codes.

### 1.2 Facial Biometrics
- **Lighting & Angle Sensitivity**: Extreme backlighting (sitting opposite windows) or low-light classrooms can degrade feature extraction quality.
- **Defensibility Response**: Capture quality checks (`quality < 0.40`) reject unreadable captures with explicit `LOW_QUALITY` codes, allowing PIN fallback or faculty inspection.
- **False Accept Rate (FAR) vs False Reject Rate (FRR)**: Threshold 0.75 represents a measured compromise for college lab environments. Increasing to 0.88 minimizes proxy risk but increases false rejections under poor lighting.

### 1.3 Dynamic QR Sharing Window
- **30-Second Snapshot Window**: If an absent student receives a photo of the QR code over high-speed 5G/Wi-Fi within 10 seconds of projection, they could submit the token before expiry.
- **Defensibility Response**: The QR factor is cross-validated with GPS and live face verification. Even if the QR code is transmitted, the absent student will fail the geofence and biometric checks.

### 1.4 Network Bandwidth in Dense Classrooms
- **Simultaneous Request Bursts**: 80–120 students in a classroom submitting check-ins concurrently within a 3-minute window can saturate local access points.
- **Defensibility Response**: Check-in payloads are lightweight JSON (<5 KB without raw images). Dynamic PIN fallback provides an alternative when camera or WebSocket bandwidth is strained.
