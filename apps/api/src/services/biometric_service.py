import json
from typing import List, Tuple, Optional
import numpy as np
from apps.api.src.core.config import settings


class BiometricVerificationService:
    """
    Institutional Face Verification Service.
    Compares live client-extracted facial embeddings against enrolled baseline embeddings
    using Normalized Cosine Similarity.
    
    Technical Trade-offs:
    - High Threshold (>= 0.85): Minimizes False Acceptance (proxies prevented), but increases False Rejection under poor lighting.
    - Balanced Threshold (0.75): Institutional standard for classroom environments (ZEAL Labs), balancing security and convenience.
    """

    @staticmethod
    def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Compute standard cosine similarity between two feature vectors:
        sim = (u . v) / (||u|| * ||v||)
        """
        u = np.array(vec1, dtype=np.float32)
        v = np.array(vec2, dtype=np.float32)

        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)

        if norm_u == 0.0 or norm_v == 0.0:
            return 0.0

        similarity = float(np.dot(u, v) / (norm_u * norm_v))
        # Clip to [-1.0, 1.0] to prevent floating point numerical overflow
        return max(-1.0, min(1.0, similarity))

    @classmethod
    def evaluate_face_evidence(
        cls,
        enrolled_reference: Optional[str],
        live_embedding: Optional[List[float]],
        capture_quality: Optional[float] = None,
        is_required: bool = True
    ) -> Tuple[str, Optional[float], str]:
        """
        Evaluates biometric live evidence against enrolled reference.
        Returns:
            - status: MATCH, MISMATCH, NOT_ENROLLED, NO_FACE, LOW_QUALITY, NOT_REQUIRED
            - similarity_score: float or None
            - reason_detail: descriptive explanation
        """
        if not is_required:
            return "NOT_REQUIRED", None, "Face verification not required for this session"

        if not enrolled_reference:
            return "NOT_ENROLLED", None, "Student has no registered biometric template on file"

        if not live_embedding or len(live_embedding) == 0:
            return "NO_FACE", None, "No face detected in live capture or empty embedding provided"

        # Check capture quality if provided
        if capture_quality is not None and capture_quality < 0.40:
            return "LOW_QUALITY", None, f"Capture quality score {capture_quality:.2f} is insufficient for reliable matching"

        try:
            ref_vector = json.loads(enrolled_reference)
            if not isinstance(ref_vector, list) or len(ref_vector) == 0:
                return "NOT_ENROLLED", None, "Enrolled biometric reference is corrupted or invalid format"

            similarity = cls.compute_cosine_similarity(live_embedding, ref_vector)
            rounded_sim = round(similarity, 4)

            threshold = settings.FACE_SIMILARITY_THRESHOLD
            if similarity >= threshold:
                return "MATCH", rounded_sim, f"Biometric match verified (similarity {rounded_sim:.2f} >= threshold {threshold:.2f})"
            else:
                return "MISMATCH", rounded_sim, f"Biometric mismatch (similarity {rounded_sim:.2f} < threshold {threshold:.2f})"
        except Exception as e:
            return "UNAVAILABLE", None, f"Biometric verification engine failure: {str(e)}"

