"""
Transfer Learning Training Pipeline — Dashboard Warning Light Classifier
Intelligent Multimodal Vehicle Breakdown Assistance and Adaptive Recovery System
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from ml.src.cv_dataset import CV_CLASSES, CLASS_TO_BREAKDOWN_CAPABILITY

torch.set_num_threads(4)


class InMemoryWarningLightDataset(Dataset):
    """Fast in-memory dataset to eliminate disk I/O bottlenecks during training."""
    def __init__(self, samples, transform=None):
        self.samples = samples  # list of (PIL.Image, label_int)
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img, label = self.samples[idx]
        if self.transform:
            img = self.transform(img)
        return img, label


class WarningLightResNet(nn.Module):
    """ResNet transfer learning model with custom classification head."""
    def __init__(self, num_classes=18, dropout_rate=0.3):
        super(WarningLightResNet, self).__init__()
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
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


def get_transforms():
    """Returns training and validation image transformation pipelines."""
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomRotation(degrees=14),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, val_transform


def load_all_images(data_dir="ml/data/cv_dataset"):
    """Loads all dataset images into memory."""
    samples = []
    classes = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
    
    for cls_idx, cls_dir_name in enumerate(classes):
        cls_path = os.path.join(data_dir, cls_dir_name)
        for fname in os.listdir(cls_path):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                fpath = os.path.join(cls_path, fname)
                with Image.open(fpath) as img:
                    samples.append((img.convert("RGB"), cls_idx))
                    
    print(f"[INFO] Loaded {len(samples)} images into memory across {len(classes)} classes.", flush=True)
    return samples


def train_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    
    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)
        
    return running_loss / total, correct / total


def evaluate_epoch(model, dataloader, criterion, device):
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []
    all_probs = []
    
    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            probs = torch.softmax(outputs, dim=1)
            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            
    return running_loss / total, correct / total, np.array(all_labels), np.array(all_preds), np.array(all_probs)


def run_training_pipeline(data_dir="ml/data/cv_dataset", models_dir="ml/models"):
    os.makedirs(models_dir, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Running CV Training on: {device}", flush=True)
    
    train_tf, val_tf = get_transforms()
    all_samples = load_all_images(data_dir)
    targets = [s[1] for s in all_samples]
    
    labels_mapping = {str(i): name for i, name in enumerate(CV_CLASSES)}
    
    # 5-Fold Stratified Cross-Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fold_accuracies = []
    fold_macro_f1s = []
    
    best_overall_val_f1 = 0.0
    best_model_state = None
    all_oof_labels, all_oof_preds, all_oof_probs = [], [], []
    
    print("\n" + "="*70, flush=True)
    print("5-FOLD STRATIFIED CROSS-VALIDATION (2-STAGE TRANSFER LEARNING)", flush=True)
    print("="*70, flush=True)
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(targets)), targets), 1):
        train_samples = [all_samples[i] for i in train_idx]
        val_samples = [all_samples[i] for i in val_idx]
        
        train_dataset = InMemoryWarningLightDataset(train_samples, transform=train_tf)
        val_dataset = InMemoryWarningLightDataset(val_samples, transform=val_tf)
        
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
        val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False, num_workers=0)
        
        # Initialize model
        model = WarningLightResNet(num_classes=len(CV_CLASSES), dropout_rate=0.3).to(device)
        criterion = nn.CrossEntropyLoss()
        
        # --- STAGE 1: Train Head Only (Conv backbone frozen) ---
        for param in model.backbone.parameters():
            param.requires_grad = False
        for param in model.backbone.fc.parameters():
            param.requires_grad = True
            
        optimizer_s1 = optim.Adam(model.backbone.fc.parameters(), lr=1e-3, weight_decay=1e-4)
        
        for epoch in range(1, 5):
            t_loss, t_acc = train_epoch(model, train_loader, criterion, optimizer_s1, device)
            v_loss, v_acc, _, _, _ = evaluate_epoch(model, val_loader, criterion, device)
            
        stage1_val_acc = v_acc
        
        # --- STAGE 2: Fine-Tuning (Unfreeze layer4 + FC head) ---
        for param in model.backbone.layer4.parameters():
            param.requires_grad = True
            
        optimizer_s2 = optim.Adam([
            {'params': model.backbone.layer4.parameters(), 'lr': 1e-4},
            {'params': model.backbone.fc.parameters(), 'lr': 3e-4}
        ], weight_decay=1e-4)
        
        for epoch in range(1, 4):
            t_loss, t_acc = train_epoch(model, train_loader, criterion, optimizer_s2, device)
            v_loss, v_acc, y_true, y_pred, y_prob = evaluate_epoch(model, val_loader, criterion, device)
            
        macro_f1 = precision_recall_fscore_support(y_true, y_pred, average='macro', zero_division=0)[2]
        fold_accuracies.append(v_acc)
        fold_macro_f1s.append(macro_f1)
        
        print(f"Fold {fold} -> Stage 1 Acc: {stage1_val_acc*100:.2f}%, Stage 2 Acc: {v_acc*100:.2f}%, Macro F1: {macro_f1:.4f}", flush=True)
        
        all_oof_labels.extend(y_true)
        all_oof_preds.extend(y_pred)
        all_oof_probs.extend(y_prob)
        
        if macro_f1 > best_overall_val_f1:
            best_overall_val_f1 = macro_f1
            best_model_state = model.state_dict()
            
    # Final Metrics across all out-of-fold validation samples
    all_oof_labels = np.array(all_oof_labels)
    all_oof_preds = np.array(all_oof_preds)
    all_oof_probs = np.array(all_oof_probs)
    
    total_acc = accuracy_score(all_oof_labels, all_oof_preds)
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(all_oof_labels, all_oof_preds, average='macro', zero_division=0)
    weighted_prec, weighted_rec, weighted_f1, _ = precision_recall_fscore_support(all_oof_labels, all_oof_preds, average='weighted', zero_division=0)
    
    print("\n" + "="*70, flush=True)
    print("FINAL OUT-OF-FOLD CROSS-VALIDATION PERFORMANCE", flush=True)
    print("="*70, flush=True)
    print(f"Overall Accuracy:  {total_acc*100:.2f}%", flush=True)
    print(f"Macro Precision:   {macro_prec:.4f}", flush=True)
    print(f"Macro Recall:      {macro_rec:.4f}", flush=True)
    print(f"Macro F1-Score:    {macro_f1:.4f}", flush=True)
    print(f"Weighted F1-Score: {weighted_f1:.4f}", flush=True)
    
    # Per-Class Breakdown
    prec_k, rec_k, f1_k, supp_k = precision_recall_fscore_support(all_oof_labels, all_oof_preds, average=None, zero_division=0)
    per_class_results = {}
    print("\nPer-Class Breakdown:", flush=True)
    for idx, name in enumerate(CV_CLASSES):
        per_class_results[name] = {
            "class_id": idx,
            "precision": round(float(prec_k[idx]), 4),
            "recall": round(float(rec_k[idx]), 4),
            "f1_score": round(float(f1_k[idx]), 4),
            "support": int(supp_k[idx])
        }
        print(f"  {idx:02d} | {name:<46} | Prec: {prec_k[idx]:.4f} | Rec: {rec_k[idx]:.4f} | F1: {f1_k[idx]:.4f} | Support: {supp_k[idx]}", flush=True)
        
    # Generate and Save Confusion Matrix Plot
    cm = confusion_matrix(all_oof_labels, all_oof_preds)
    plt.figure(figsize=(14, 11))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=[c[:16] for c in CV_CLASSES],
                yticklabels=[c[:16] for c in CV_CLASSES])
    plt.title('Vehicle Dashboard Warning Light Recognition — Confusion Matrix', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Predicted Warning Light Class', fontsize=12, fontweight='bold')
    plt.ylabel('Ground Truth Class', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    cm_path = os.path.join(models_dir, "cv_confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"\n[SAVED] Confusion Matrix Plot: {cm_path}", flush=True)
    
    # Save Model Weights
    model_path = os.path.join(models_dir, "cv_model.pt")
    torch.save(best_model_state, model_path)
    print(f"[SAVED] Champion CV PyTorch Weights: {model_path} ({os.path.getsize(model_path)/(1024*1024):.2f} MB)", flush=True)
    
    # Save Labels Mapping
    labels_path = os.path.join(models_dir, "cv_labels.json")
    with open(labels_path, "w") as f:
        json.dump(labels_mapping, f, indent=2)
    print(f"[SAVED] Labels Mapping: {labels_path}", flush=True)
    
    # Save Preprocessing Config
    config_path = os.path.join(models_dir, "cv_preprocessing_config.json")
    cv_config = {
        "model_architecture": "ResNet18-TransferLearning",
        "num_classes": len(CV_CLASSES),
        "input_resolution": [224, 224],
        "input_channels": 3,
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        },
        "color_mode": "RGB",
        "supported_formats": ["JPEG", "PNG", "WEBP"],
        "confidence_threshold_recommended": 0.65,
        "uncertainty_guidance": "If confidence is below 0.65, prompt user to retake photo with better centering and glare-free illumination."
    }
    with open(config_path, "w") as f:
        json.dump(cv_config, f, indent=2)
    print(f"[SAVED] Preprocessing Config: {config_path}", flush=True)
    
    # Save Comprehensive Metrics JSON
    metrics_path = os.path.join(models_dir, "cv_metrics.json")
    full_metrics = {
        "model_name": "dashboard-warning-light-resnet18-v1",
        "dataset_name": "Roboflow Car Dashboard Warning Lights (CC BY 4.0)",
        "total_samples": len(all_oof_labels),
        "validation_strategy": "5-Fold Stratified Cross-Validation",
        "overall_accuracy": round(float(total_acc), 4),
        "macro_precision": round(float(macro_prec), 4),
        "macro_recall": round(float(macro_rec), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "fold_accuracies": [round(float(a), 4) for a in fold_accuracies],
        "fold_macro_f1s": [round(float(f), 4) for f in fold_macro_f1s],
        "per_class_breakdown": per_class_results
    }
    with open(metrics_path, "w") as f:
        json.dump(full_metrics, f, indent=2)
    print(f"[SAVED] CV Metrics JSON: {metrics_path}", flush=True)
    
    return full_metrics


if __name__ == "__main__":
    run_training_pipeline()
