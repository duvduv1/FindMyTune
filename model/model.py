# model/model.py

import os
import numpy as np
import torch
from torch import nn, optim
from torch.utils.data import Dataset, DataLoader
from torch.cuda.amp import GradScaler, autocast

from database.song_database import SongDatabase
from settings import MODEL_PATH

NUM_CLASSES = 628
N_MELS = 128

# -----------------------------
# 1) Contrastive (pretrain) Dataset
# -----------------------------
class SongContrastiveDataset(Dataset):
    def __init__(self, song_db: SongDatabase):
        self.triplets = []  # (clean, noisy, reverb)
        self.pairs    = []  # all possible pairs

        # Load (id, spectrogram_folder) tuples
        songs = song_db.get_columns("id, spectrograms")
        for song_id, folder in songs:
            parts = {}
            for fn in os.listdir(folder):
                if fn.endswith(".npy"):
                    part_id, version = fn[:-4].split("_")  # e.g. "part3", "clean"
                    parts.setdefault(part_id, {})[version] = os.path.join(folder, fn)

            # build triplets & pairs
            for vers in parts.values():
                if {"clean","noisy","reverb"} <= set(vers):
                    self.triplets.append((vers["clean"], vers["noisy"], vers["reverb"]))
                # all unordered pairs
                vlist = list(vers.items())
                for i in range(len(vlist)):
                    for j in range(i+1, len(vlist)):
                        self.pairs.append((vlist[i][1], vlist[j][1]))

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        p1, p2 = self.pairs[idx]
        spec1 = torch.tensor(np.load(p1), dtype=torch.float32).unsqueeze(0)
        spec2 = torch.tensor(np.load(p2), dtype=torch.float32).unsqueeze(0)
        return spec1, spec2


# -----------------------------
# 2) Classification Dataset
# -----------------------------
class SongSpectrogramDataset(Dataset):
    def __init__(self, song_db: SongDatabase):
        self.data   = []
        self.labels = []
        self.labels_to_songs = {}
        self.songs_to_labels = {}

        records = song_db.get_columns("id, spectrograms, song_name")
        for song_id, folder, name in records:
            self.labels_to_songs[song_id] = name
            self.songs_to_labels[name] = song_id
            for fn in os.listdir(folder):
                if fn.endswith(".npy"):
                    self.data.append(os.path.join(folder, fn))
                    self.labels.append(song_id)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        spec = np.load(self.data[idx])
        # fix: N_MELS is now defined
        if spec.shape not in {(128,216), (N_MELS,216)}:
            raise ValueError(f"Unexpected shape {spec.shape}")
        tensor = torch.tensor(spec, dtype=torch.float32).unsqueeze(0)  # [1,128,216]
        label  = self.labels[idx]
        return tensor, label


# -----------------------------
# 3) CNN Model
# -----------------------------
class SongCNN(nn.Module):
    def __init__(self, num_classes=NUM_CLASSES):
        super().__init__()
        self.conv_block1 = nn.Sequential(
            nn.Conv2d(1,32,3,padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout2d(0.2)
        )
        self.conv_block2 = nn.Sequential(
            nn.Conv2d(32,64,3,padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout2d(0.2)
        )
        self.conv_block3 = nn.Sequential(
            nn.Conv2d(64,128,3,padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2), nn.Dropout2d(0.2)
        )
        self.conv_block4 = nn.Sequential(
            nn.Conv2d(128,256,3,padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.global_avg = nn.AdaptiveAvgPool2d((1,1))
        self.fc = nn.Sequential(
            nn.Linear(256,1024), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(1024,512), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(512,num_classes)
        )

    def extract_features(self, x):
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        x = self.conv_block3(x)
        x = self.conv_block4(x)
        x = self.global_avg(x)
        return x.flatten(1)

    def forward(self, x):
        x = self.extract_features(x)
        return self.fc(x)


# -----------------------------
# 4) Contrastive Loss
# -----------------------------
class ContrastiveLoss(nn.Module):
    def __init__(self, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, x1, x2):
        z1 = nn.functional.normalize(x1, dim=1)
        z2 = nn.functional.normalize(x2, dim=1)
        logits = torch.mm(z1, z2.t()) / self.temperature
        labels = torch.arange(z1.size(0), device=z1.device)
        return nn.CrossEntropyLoss()(logits, labels)


# -----------------------------
# 5) Pretrain (Contrastive)
# -----------------------------
def pretrain_contrastive(model, dataset, model_path,
                         batch_size=32, lr=1e-3, epochs=10):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True,
                            num_workers=4, pin_memory=True)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    scaler = GradScaler()

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for spec1, spec2 in dataloader:
            spec1, spec2 = spec1.to(device), spec2.to(device)
            optimizer.zero_grad()
            with autocast():
                z1 = model.extract_features(spec1)
                z2 = model.extract_features(spec2)
                loss = ContrastiveLoss()(z1, z2)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            total_loss += loss.item()
        avg = total_loss / len(dataloader)
        print(f"[Pretrain] Epoch {epoch+1}/{epochs}, Loss={avg:.4f}")
        scheduler.step(avg)
    torch.save(model.state_dict(), model_path)
    print(f"Saved pretrained model to {model_path}")


# -----------------------------
# 6) Train Classification
# -----------------------------
def train(model, dataset, model_path,
          batch_size=32, lr=1e-3, epochs=10):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True,
                            num_workers=4, pin_memory=True)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3, factor=0.5)
    scaler = GradScaler()

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = total = 0
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            with autocast():
                outputs = model(inputs)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        avg_loss = running_loss / len(dataloader)
        acc = correct / total * 100.0
        print(f"[Train] Epoch {epoch+1}/{epochs}, Loss={avg_loss:.4f}, Acc={acc:.2f}%")
        scheduler.step(avg_loss)

    torch.save({
        'model_state_dict': model.state_dict(),
        'num_classes': NUM_CLASSES,
        'labels_to_songs': dataset.labels_to_songs,
        'songs_to_labels': dataset.songs_to_labels
    }, model_path)
    print(f"Saved classification model to {model_path}")


# -----------------------------
# 7) Entry Points
# -----------------------------
def pretrain_model(song_db: SongDatabase):
    print("Starting contrastive pretraining...")
    dataset = SongContrastiveDataset(song_db)
    model = SongCNN()
    pretrain_contrastive(model, dataset, model_path="contrastive_pretrained_model")


def create_model(song_db: SongDatabase, model_path: str, pretrained: bool = True):
    print("Preparing classification dataset...")
    dataset = SongSpectrogramDataset(song_db)
    model = SongCNN()
    if pretrained:
        print("Loading pretrained weights...")
        model.load_state_dict(torch.load("contrastive_pretrained_model", map_location='cpu'))
    train(model, dataset, model_path, batch_size=32, lr=1e-3, epochs=25)


def continue_training(old_path: str, new_path: str, song_db: SongDatabase, extra_epochs: int = 10):
    print("Continuing training from", old_path)
    checkpoint = torch.load(old_path, map_location='cpu')
    model = SongCNN()
    model.load_state_dict(checkpoint['model_state_dict'])
    dataset = SongSpectrogramDataset(song_db)
    train(model, dataset, new_path, batch_size=32, lr=5e-4, epochs=extra_epochs)
