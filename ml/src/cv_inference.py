"""
Computer Vision Inference Interface — Dashboard Warning Light Recognition
Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System
"""

import os
import json
import io
from pathlib import Path
from typing import Dict, Any, Union, BinaryIO
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms, models


MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


# Mapping to Vehicle Breakdown Decision Capabilities
CLASS_TO_BREAKDOWN_CAPABILITY = {
    "Battery Alert Light": {"capability": "battery_jumpstart", "fault": "Low Voltage / Electrical Failure", "severity": "HIGH"},
    "Check Engine Light": {"capability": "engine_repair", "fault": "Engine Emissions / Combustion Fault", "severity": "HIGH"},
    "Engine Temperature Warning Light": {"capability": "towing", "fault": "Engine Thermal Overheating", "severity": "CRITICAL"},
    "Oil Pressure Warning Light": {"capability": "towing", "fault": "Critical Oil Pressure Loss", "severity": "CRITICAL"},
    "Brake Warning Light": {"capability": "towing", "fault": "Brake System Failure / Hydraulic Loss", "severity": "CRITICAL"},
    "Tire Pressure Warning Light": {"capability": "tire_change", "fault": "Tire Puncture / Pressure Drop", "severity": "HIGH"},
    "Transmission Temperature Warning": {"capability": "towing", "fault": "Transmission Overheating", "severity": "CRITICAL"},
    "Anti-lock Braking System (ABS) Warning Light": {"capability": "engine_repair", "fault": "ABS Sensor / Controller Anomaly", "severity": "MEDIUM"},
    "Low Fuel Warning Light": {"capability": "battery_jumpstart", "fault": "Fuel Starvation Alert", "severity": "LOW"},
    "Airbag Indicator Light": {"capability": "engine_repair", "fault": "SRS Restraint System Alert", "severity": "LOW"},
    "Traction Control Light": {"capability": "engine_repair", "fault": "Stability Control Active / Fault", "severity": "LOW"},
    "Traction Control Malfunction": {"capability": "engine_repair", "fault": "Traction Module Malfunction", "severity": "MEDIUM"},
    "Automatic Shift Lock / Engine Start Indicator": {"capability": "engine_repair", "fault": "Shift Interlock Warning", "severity": "LOW"},
    "Fog Lamp Indicator": {"capability": None, "fault": "Auxiliary Lighting Status", "severity": "LOW"},
    "Lane Departure Warning": {"capability": None, "fault": "ADAS Camera / Lane Alert", "severity": "LOW"},
    "Seat Belt Reminder": {"capability": None, "fault": "Occupant Restraint Reminder", "severity": "LOW"},
    "Security Indicator Light": {"capability": "engine_repair", "fault": "Immobilizer / Anti-Theft Lockout", "severity": "MEDIUM"},
    "Washer Fluid Reminder": {"capability": None, "fault": "Washer Reservoir Depleted", "severity": "LOW"}
}


class WarningLightResNet(nn.Module):
    """ResNet transfer learning model architecture matching trained weights."""
    def __init__(self, num_classes=18, dropout_rate=0.3):
        super(WarningLightResNet, self).__init__()
        self.backbone = models.resnet18(weights=None)
        num_features = self.backbone.fc.in_features  # 512
        
        self.backbone.fc = nn.Sequential(
            nn.Dropout(p=dropout_rate),
            nn.Linear(num_features, 256),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(256),
            nn.Dropout(p=dropout_rate / 2),
            nn.Linear(256, num_classes)
        )
        
    def forward(self, x):
        return self.backbone(x)


class WarningLightPredictor:
    """
    Production-ready inference class for vehicle dashboard warning light recognition.
    Designed for FastAPI backend integration in POST /vision/analyze.
    """
    CONFIDENCE_THRESHOLD = 0.65

    def __init__(self, models_dir: Union[str, Path] = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 1. Load Labels
        labels_path = self.models_dir / "cv_labels.json"
        with open(labels_path, "r") as f:
            self.labels = json.load(f)
            
        # 2. Load Preprocessing Config
        config_path = self.models_dir / "cv_preprocessing_config.json"
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
        # 3. Load Model
        self.model = WarningLightResNet(num_classes=len(self.labels), dropout_rate=0.3)
        weights_path = self.models_dir / "cv_model.pt"
        state_dict = torch.load(weights_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        # 4. Standard Preprocessing Transform
        norm = self.config["normalization"]
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=norm["mean"], std=norm["std"])
        ])

    def predict(self, image_input: Union[str, Path, bytes, BinaryIO, Image.Image]) -> Dict[str, Any]:
        """
        Runs warning light recognition on an input dashboard photo.
        
        Args:
            image_input: File path (str/Path), raw bytes, file-like object, or PIL Image.
            
        Returns:
            Dict containing predicted warning light class, confidence, probabilities,
            recommended breakdown capability, and uncertainty flags.
        """
        # Load and validate PIL Image
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input)
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input))
        elif hasattr(image_input, "read"):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        img_rgb = img.convert("RGB")

        # Transform and batch
        tensor = self.transform(img_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        class_id = int(probs.argmax())
        confidence = float(probs[class_id])
        class_name = self.labels[str(class_id)]

        breakdown_info = CLASS_TO_BREAKDOWN_CAPABILITY.get(class_name, {
            "capability": "engine_repair", "fault": class_name, "severity": "MEDIUM"
        })

        is_uncertain = confidence < self.CONFIDENCE_THRESHOLD

        return {
            "class_id": class_id,
            "warning_light": class_name,
            "confidence": round(confidence, 4),
            "is_uncertain": is_uncertain,
            "guidance": "Confidence below threshold; please retake with clear dashboard lighting." if is_uncertain else "High confidence recognition.",
            "recommended_capability": breakdown_info["capability"],
            "indicated_fault": breakdown_info["fault"],
            "severity": breakdown_info["severity"],
            "class_probabilities": {
                self.labels[str(i)]: round(float(probs[i]), 4)
                for i in range(len(probs))
            }
        }


if __name__ == "__main__":
    predictor = WarningLightPredictor()
    # Test on generated sample
    test_img = Image.open("ml/data/cv_dataset/03_Battery_Alert_Light/sample_000.jpg")
    res = predictor.predict(test_img)
    print("Test CV Prediction:")
    print(json.dumps({k: v for k, v in res.items() if k != "class_probabilities"}, indent=2))
