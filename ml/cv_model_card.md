
# Computer Vision Model Card: Dashboard Warning Light Classifier

**Model Name**: `dashboard-warning-light-resnet18-v1`  
**Task**: Multi-Class Image Classification (Automotive Dashboard Warning Light Recognition)  
**Framework**: PyTorch 2.13+ / Torchvision  
**Architecture**: 2-Stage Transfer Learning with ResNet-18 Backbone & Custom Dropout/BatchNorm Classifier Head  
**Author / Maintainer**: Vishal (ML Module Lead)  
**Last Updated**: September 2026  

---

## 1. Purpose & System Context

This computer vision model recognizes illuminated instrument cluster warning lights from driver-captured photos. 

Within the **Intelligent Multimodal Vehicle Breakdown Assistance System**, this module replaces manual text dropdown inputs (`warning_light`) in the intake form with automated visual verification from a photo. The inferred warning light directly feeds into the downstream breakdown decision flow (`battery_jumpstart`, `engine_repair`, `tire_change`, `towing`) and provides cross-modal validation with the OBD-II engine sensor diagnostic model.

---

## 2. Input Specification

| Property | Requirement / Value | Notes |
|:---|:---:|:---|
| **Supported Formats** | JPEG, PNG, WEBP | Standard mobile/browser uploads |
| **Input Dimensions** | `224 × 224` pixels | Resized via bilinear interpolation |
| **Color Channels** | 3 (RGB) | Converted from RGBA/Grayscale automatically |
| **Pixel Value Range** | `[0.0, 1.0]` | Scaled from standard `[0, 255]` |
| **Normalization Mean** | `[0.485, 0.456, 0.406]` | ImageNet standard mean |
| **Normalization Std** | `[0.229, 0.224, 0.225]` | ImageNet standard standard deviation |
| **Capture Guidance** | Centered, lit, steady | Camera positioned 20–40 cm from instrument cluster, avoiding heavy flash glare |

---

## 3. Output Specification

The model returns a structured JSON dictionary:

```json
{
  "class_id": 3,
  "warning_light": "Battery Alert Light",
  "confidence": 0.9981,
  "is_uncertain": false,
  "guidance": "High confidence recognition.",
  "recommended_capability": "battery_jumpstart",
  "indicated_fault": "Low Voltage / Electrical Failure",
  "severity": "HIGH",
  "class_probabilities": {
    "Battery Alert Light": 0.9981,
    "Check Engine Light": 0.0008,
    "Brake Warning Light": 0.0003,
    "...": 0.0
  }
}
```

---

## 4. Label Schema & Breakdown Assistance Mappings

The model covers **18 standard automotive warning lights** (Roboflow Universe / ISO 7000):

| ID | Warning Light Label | Automotive Indication | Breakdown Capability | Severity |
|:---:|:---|:---|:---:|:---:|
| `0` | **Airbag Indicator Light** | Supplemental Restraint System (SRS) fault | `engine_repair` | `LOW` |
| `1` | **Anti-lock Braking System (ABS)** | Wheel speed sensor / ABS module malfunction | `engine_repair` | `MEDIUM` |
| `2` | **Automatic Shift Lock / Start** | Transmission interlock / clutch switch anomaly | `engine_repair` | `LOW` |
| `3` | **Battery Alert Light** | Alternator failure, charging system fault, low voltage | `battery_jumpstart` | `HIGH` |
| `4` | **Brake Warning Light** | Low brake fluid, parking brake on, hydraulic drop | `towing` | `CRITICAL` |
| `5` | **Check Engine Light** | Emission anomaly, sensor misfire, combustion fault | `engine_repair` | `HIGH` |
| `6` | **Engine Temperature Warning** | Radiator boiling, coolant loss, thermal overheat | `towing` | `CRITICAL` |
| `7` | **Fog Lamp Indicator** | Auxiliary fog lighting status indicator | `None` (Advisory) | `LOW` |
| `8` | **Lane Departure Warning** | ADAS camera lane tracking warning | `None` (Advisory) | `LOW` |
| `9` | **Low Fuel Warning Light** | Fuel level critical (starvation risk) | `battery_jumpstart` | `LOW` |
| `10` | **Oil Pressure Warning Light** | Critical loss of lubrication pressure | `towing` | `CRITICAL` |
| `11` | **Seat Belt Reminder** | Driver / passenger restraint unbuckled | `None` (Advisory) | `LOW` |
| `12` | **Security Indicator Light** | Immobilizer key lockout / anti-theft trigger | `engine_repair` | `MEDIUM` |
| `13` | **Tire Pressure Warning Light** | TPMS alert, flat tire or severe pressure loss | `tire_change` | `HIGH` |
| `14` | **Traction Control Light** | Wheel slip active or temporary ESP intervention | `engine_repair` | `LOW` |
| `15` | **Traction Control Malfunction** | ESP / Stability control unit hardware fault | `engine_repair` | `MEDIUM` |
| `16` | **Transmission Temperature** | Automatic gearbox fluid overheating | `towing` | `CRITICAL` |
| `17` | **Washer Fluid Reminder** | Windshield washer fluid reservoir depleted | `None` (Advisory) | `LOW` |

---

## 5. Confidence Meaning & Threshold Policy

- **Confidence Score**: Softmax output probability `P(Class | Image) ∈ [0.0, 1.0]`.
- **Recommended Decision Threshold (`CONFIDENCE_THRESHOLD = 0.65`)**:
  - **`Confidence ≥ 0.65` (`is_uncertain: false`)**: High confidence detection; automatically autofill the warning light and trigger matching.
  - **`Confidence < 0.65` (`is_uncertain: true`)**: Uncertain classification; backend/frontend should prompt driver: *"Photo is blurry or dimly lit. Please confirm the detected light or take a clearer photo."*

---

## 6. Evaluation Performance & Metrics

Evaluated using **5-Fold Stratified Cross-Validation** (630 total augmented samples, 35 samples per class):

### Overall Performance

| Metric | Score |
|:---|:---:|
| **Overall Accuracy** | **89.05%** |
| **Macro Precision** | **0.8916** |
| **Macro Recall** | **0.8905** |
| **Macro F1-Score** | **0.8893** |
| **Weighted F1-Score** | **0.8893** |

### 5-Fold Stratified Cross-Validation Progression

| Fold | Stage 1 Accuracy (Head Only) | Stage 2 Accuracy (Fine-Tuning) | Macro F1-Score |
|:---:|:---:|:---:|:---:|
| **Fold 1** | 88.10% | 88.89% | 0.8622 |
| **Fold 2** | 85.71% | 90.48% | 0.9026 |
| **Fold 3** | 87.30% | 87.30% | 0.8660 |
| **Fold 4** | 80.95% | 88.10% | 0.8666 |
| **Fold 5** | 83.33% | 90.48% | 0.8843 |
| **Mean ± Std** | **85.08% ± 2.68%** | **89.05% ± 1.28%** | **0.8763 ± 0.0152** |

### Per-Class Evaluation Breakdown

| Class ID | Warning Light Class | Precision | Recall | F1-Score | Validation Support |
|:---:|:---|:---:|:---:|:---:|:---:|
| `00` | Airbag Indicator Light | 1.0000 | 1.0000 | **1.0000** | 35 |
| `01` | Anti-lock Braking System (ABS) | 1.0000 | 1.0000 | **1.0000** | 35 |
| `02` | Automatic Shift Lock / Start | 1.0000 | 1.0000 | **1.0000** | 35 |
| `03` | Battery Alert Light | 1.0000 | 1.0000 | **1.0000** | 35 |
| `04` | Brake Warning Light | 1.0000 | 0.9714 | **0.9855** | 35 |
| `05` | Check Engine Light | 1.0000 | 1.0000 | **1.0000** | 35 |
| `06` | Engine Temperature Warning | 0.5000 | 0.6571 | **0.5679** | 35 |
| `07` | Fog Lamp Indicator | 1.0000 | 1.0000 | **1.0000** | 35 |
| `08` | Lane Departure Warning | 1.0000 | 1.0000 | **1.0000** | 35 |
| `09` | Low Fuel Warning Light | 1.0000 | 1.0000 | **1.0000** | 35 |
| `10` | Oil Pressure Warning Light | 1.0000 | 1.0000 | **1.0000** | 35 |
| `11` | Seat Belt Reminder | 1.0000 | 1.0000 | **1.0000** | 35 |
| `12` | Security Indicator Light | 1.0000 | 1.0000 | **1.0000** | 35 |
| `13` | Tire Pressure Warning Light | 1.0000 | 1.0000 | **1.0000** | 35 |
| `14` | Traction Control Light | 0.5122 | 0.6000 | **0.5526** | 35 |
| `15` | Traction Control Malfunction | 0.5172 | 0.4286 | **0.4688** | 35 |
| `16` | Transmission Temperature | 0.5200 | 0.3714 | **0.4333** | 35 |
| `17` | Washer Fluid Reminder | 1.0000 | 1.0000 | **1.0000** | 35 |

---

## 7. Ready-to-Use Backend Integration Code

FastAPI backend developers (Ujwal) can copy and paste this self-contained class directly:

```python
from pathlib import Path
from typing import Dict, Any, Union, BinaryIO
import io
import json
from PIL import Image
import torch
import torch.nn as nn
from torchvision import transforms, models

# Path to trained artifacts
MODELS_DIR = Path(__file__).resolve().parents[2] / "ml" / "models"


class WarningLightResNet(nn.Module):
    def __init__(self, num_classes=18, dropout_rate=0.3):
        super().__init__()
        self.backbone = models.resnet18(weights=None)
        num_features = self.backbone.fc.in_features
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
    CONFIDENCE_THRESHOLD = 0.65

    def __init__(self, models_dir: Union[str, Path] = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        with open(self.models_dir / "cv_labels.json", "r") as f:
            self.labels = json.load(f)
            
        with open(self.models_dir / "cv_preprocessing_config.json", "r") as f:
            self.config = json.load(f)
            
        self.model = WarningLightResNet(num_classes=len(self.labels), dropout_rate=0.3)
        state_dict = torch.load(self.models_dir / "cv_model.pt", map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        norm = self.config["normalization"]
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=norm["mean"], std=norm["std"])
        ])

    def predict(self, image_input: Union[str, Path, bytes, BinaryIO, Image.Image]) -> Dict[str, Any]:
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

        tensor = self.transform(img.convert("RGB")).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        class_id = int(probs.argmax())
        confidence = float(probs[class_id])
        class_name = self.labels[str(class_id)]
        is_uncertain = confidence < self.CONFIDENCE_THRESHOLD

        return {
            "class_id": class_id,
            "warning_light": class_name,
            "confidence": round(confidence, 4),
            "is_uncertain": is_uncertain,
            "class_probabilities": {
                self.labels[str(i)]: round(float(probs[i]), 4)
                for i in range(len(probs))
            }
        }
```

---

## 8. Failure Conditions & Handling Policy

1. **Blurry / Dark Image**: Returns low confidence (`< 0.65`), triggering `is_uncertain: true`. The API should return an advisory asking for a clearer photo.
2. **Unsupported Format / Corrupted Bytes**: `Image.open` throws an error caught with HTTP 400 (`"Invalid or corrupt image payload"`).
3. **No Dashboard Light Present**: All class probabilities remain uniformly low (`< 0.20`), triggering an uncertainty alert.
4. **Multiple Warning Lights Lit**: Current architecture predicts the **dominant illuminated symbol**; future milestone may extend to multi-label BCEWithLogitsLoss.

---

## 9. Multimodal Decision Pipeline Fusion Proposal (For Backend - Ujwal)

When integrating both the **Telemetry Diagnostic Model (`model.pkl`)** and the **Warning Light CV Model (`cv_model.pt`)**:

```
                              ┌──────────────────────────────────┐
                              │ Driver Submits Breakdown Request │
                              └────────────────┬─────────────────┘
                                               │
                   ┌───────────────────────────┴───────────────────────────┐
                   ▼                                                       ▼
        ┌───────────────────────┐                               ┌──────────────────────┐
        │ Telemetry Model (ML)  │                               │ Vision Model (CV)    │
        │ Sensor Features       │                               │ Dashboard Photo      │
        └──────────┬────────────┘                               └──────────┬───────────┘
                   ▼                                                       ▼
         Predicted Engine Fault                                   Detected Warning Light
        (e.g., "Low Voltage")                                   (e.g., "Battery Alert")
                   │                                                       │
                   └───────────────────────────┬───────────────────────────┘
                                               ▼
                              ┌──────────────────────────────────┐
                              │   Multimodal Agreement Matrix    │
                              └────────────────┬─────────────────┘
                                               │
             ┌─────────────────────────────────┼─────────────────────────────────┐
             ▼                                 ▼                                 ▼
   [ AGREEMENT DETECTED ]            [ PARTIAL CORROBORATION ]           [ CONFLICT / DIVERGENCE ]
   • Telemetry = Low Voltage         • Telemetry = Lean Mixture          • Telemetry = No Fault
   • Vision = Battery Alert          • Vision = Check Engine             • Vision = Engine Temp Warning
   ─────────────────────────         ──────────────────────────          ─────────────────────────
   Confidence boosted to 99%         Severity: Medium (Engine Repair)    Flag warning & dispatch
   Immediate Battery Dispatch        Normal diagnostic flow              emergency towing for overheat
```

1. **Cross-Modal Confirmation**: If `Battery Alert Light` (CV) matches `Low Voltage` (Telemetry), elevate confidence to **0.99** and directly schedule `battery_jumpstart`.
2. **Discrepancy Resolution**: If `No Fault` is predicted from telemetry but the CV model detects `Engine Temperature Warning Light` or `Oil Pressure Warning Light`, prioritize the physical safety visual indicator (`CRITICAL` severity / `towing`).
