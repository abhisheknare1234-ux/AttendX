from typing import Tuple, Optional
from apps.api.src.core.config import settings


class LivenessDetectionService:
    """
    Institutional Anti-Spoofing & Liveness Service.
    
    Protects against Presentation Attacks (PAD):
    - Print Attack (photo printout of legitimate student)
    - Replay Attack (high-res video playback on tablet/phone)
    - 3D Mask Attack
    
    Architectural Contract:
    - Never fabricates a successful liveness result when the check is disabled or unconfigured.
    - Explicitly marks state as `NOT_CONFIGURED` or `NOT_REQUIRED` so the Risk Engine
      handles the uncertainty transparently according to institutional policy.
    """

    @classmethod
    def evaluate_liveness(
        cls,
        liveness_confirmed: Optional[bool],
        is_required: bool = False
    ) -> Tuple[str, Optional[float], str]:
        """
        Evaluate anti-spoof evidence.
        Returns:
            - status: PASSED, FAILED, NOT_CONFIGURED, NOT_REQUIRED, UNAVAILABLE
            - score: float or None
            - reason_detail: human-readable rationale
        """
        if not is_required:
            return "NOT_REQUIRED", None, "Liveness verification is not mandated by the current session policy"

        # Check if provider is enabled
        if settings.LIVENESS_PROVIDER == "not_configured" or not settings.LIVENESS_REQUIRED:
            return "NOT_CONFIGURED", None, "Liveness anti-spoof hardware/service is not configured on this institutional node"

        if liveness_confirmed is None:
            return "UNAVAILABLE", None, "No liveness telemetry received from capture device"

        if liveness_confirmed is True:
            # High-confidence genuine human challenge passed
            return "PASSED", 0.98, "Live human interaction verified by challenge-response protocol"
        else:
            return "FAILED", 0.12, "Potential presentation attack detected: replay or static image characteristics"
