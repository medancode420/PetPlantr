from __future__ import annotations

from typing import Any, Dict, List

class BreedInferenceEngine:
	"""Minimal stub for development/tests.
	Real implementation should load models and perform inference.
	"""

	def __init__(self) -> None:
		self._loaded = False
		self._version = "stub-0.1"
		self._breeds: List[str] = [
			"labrador", "poodle", "bulldog", "beagle", "german_shepherd"
		]

	async def load_model(self) -> None:
		self._loaded = True

	async def predict(self, image: Any, use_tta: bool, confidence_threshold: float, top_k: int) -> Dict[str, Any]:
		# Return deterministic stub result
		preds = [{"labrador": 0.91}, {"poodle": 0.05}, {"beagle": 0.04}]
		flat = [{"breed": k, "confidence": v} for d in preds for k, v in d.items()]
		flat = sorted(flat, key=lambda x: x["confidence"], reverse=True)
		top = flat[:top_k]
		return {
			"predicted_breed": top[0]["breed"],
			"confidence": top[0]["confidence"],
			"top_predictions": [{t["breed"]: t["confidence"]} for t in top],
			"is_high_confidence": top[0]["confidence"] >= confidence_threshold,
			"model_version": self._version,
		}

	def get_model_info(self) -> Dict[str, Any]:
		return {"model_version": self._version, "loaded": self._loaded}

	def get_supported_breeds(self) -> List[str]:
		return self._breeds

	def update_calibration(self, calibration_data: List[Dict[str, Any]]) -> None:
		# no-op in stub
		return

	def get_performance_metrics(self) -> Dict[str, Any]:
		return {"requests_total": 0}

