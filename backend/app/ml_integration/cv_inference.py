import base64
import binascii
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Project root:
# vehicle-breakdown-assist/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Allow the backend to import the project's ML package
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load the CV model lazily.
# This prevents the model from loading until an image is actually analyzed.
_predictor: Optional[Any] = None


def _get_predictor() -> Any:
    global _predictor

    if _predictor is None:
        try:
            from ml.src.cv_inference import WarningLightPredictor
            _predictor = WarningLightPredictor()
        except ImportError as e:
            raise ValueError(f"Computer Vision inference module unavailable ({e})")

    return _predictor


def analyze_warning_light(
    engine_photo: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    Analyze a dashboard/vehicle image using the CV warning-light model.

    The frontend sends the image as a base64 Data URL, for example:

        data:image/jpeg;base64,<encoded-image>

    Raw base64 strings are also supported.

    Returns:
        CV prediction dictionary when an image is supplied.
        None when no image is supplied.
    """

    if not engine_photo:
        return None

    try:
        # Remove the Data URL prefix if present.
        if "," in engine_photo:
            _, encoded_image = engine_photo.split(",", 1)
        else:
            encoded_image = engine_photo

        # Convert base64 → raw image bytes.
        image_bytes = base64.b64decode(
            encoded_image,
            validate=True,
        )

        if not image_bytes:
            raise ValueError("Decoded image data is empty.")

        # Run Vishal's trained CV model.
        predictor = _get_predictor()

        result = predictor.predict(image_bytes)

        return result

    except (ValueError, binascii.Error) as exc:
        raise ValueError(
            f"Invalid dashboard image data: {exc}"
        ) from exc