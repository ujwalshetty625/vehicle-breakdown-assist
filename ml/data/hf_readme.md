---
license: mit
library_name: pytorch
pipeline_tag: image-classification
tags:
  - computer-vision
  - image-classification
  - automotive
  - onnx
  - pytorch
  - resnet
datasets:
  - custom
---

# Make sure git-xet is installed (https://hf.co/docs/hub/git-xet)
brew install git-xet
git xet install

git clone https://huggingface.co/asahiner/car-warning-light-detection

# If you want to clone without large files - just their pointers
GIT_LFS_SKIP_SMUDGE=1 git clone https://huggingface.co/asahiner/car-warning-light-detection

# Make sure the hf CLI is installed
curl -LsSf https://hf.co/cli/install.sh | bash

# Download the model
hf download asahiner/car-warning-light-detection

---
# 🚗 Car Warning Light Detection

An open-source deep learning model that detects and classifies **vehicle dashboard warning lights** from images.

The model supports both **mobile inference (ONNX)** and **web/server inference (PyTorch)** and is designed to work in real-world conditions with multiple warning lights visible at once.

---

## 🔍 What it does

- Detects **multiple warning lights** in a single dashboard image
- Classifies **68 different warning light types**
- Provides **confidence scores**
- Designed for **AI-assisted vehicle diagnostics**
- Works with:
  - 📱 Mobile apps (ONNX)
  - 🌐 Web / backend servers (PyTorch)

---

## 🖼️ Demo / Screenshots

![Screenshot_20260115_023301](https://cdn-uploads.huggingface.co/production/uploads/6846182a2f480d94263019f4/jNc5NlCi99OHELmGcuOvH.png)
![Screenshot_20260115_023408](https://cdn-uploads.huggingface.co/production/uploads/6846182a2f480d94263019f4/8-pg-GFnyFkw-6ij0ptji.png)
![Screenshot_20260115_023449](https://cdn-uploads.huggingface.co/production/uploads/6846182a2f480d94263019f4/w9eSlpju1YurUwhKXjlI1.png)

---

## 🧠 Model Architecture

- **Backbone**: ResNet50
- **Input size**: `3 × 224 × 224`
- **Head**:
  - Dropout (0.3)
  - Linear (2048 → 512)
  - ReLU
  - BatchNorm
  - Dropout (0.15)
  - Linear (512 → 68)
- **Parameters**: ~24.6M

Architecture definition:  
📄 `model_architecture.py`

---

## 📦 Files

| File | Description |
|-----|------------|
| `car_warning_lights_resnet50.pth` | PyTorch weights (web/server inference) |
| `car_warning_lights_resnet50.onnx` | ONNX model (mobile / edge inference) |
| `model_architecture.py` | Model definition |
| `README.md` | Model documentation |

---

## 🚀 Usage

### PyTorch
```python
import torch
from model_architecture import create_model

model = create_model(num_classes=68)
model.load_state_dict(
    torch.load("car_warning_lights_resnet50.pth", map_location="cpu")
)
model.eval()
