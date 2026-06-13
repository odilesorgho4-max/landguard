"""
============================================================
 LandGuard Neuro-Symbolic AI
 neural_model.py — Module neuronal PyTorch (Partie 4)
 Classification : STANDARD | ATYPIQUE | SPECULATEUR | FRAUDEUR_PROBABLE
============================================================
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from pathlib import Path

# ============================================================
# SECTION 1 : Classes et features
# ============================================================

CLASSES = ["standard", "atypique", "speculateur", "fraude"]
N_CLASSES = len(CLASSES)

FEATURE_NAMES = [
    "nb_parcelles",       # entier : nombre total de parcelles détenues
    "frequence_revente",  # float  : nb reventes / nb parcelles
    "ratio_plus_value",   # float  : (prix_vente - prix_achat) / prix_achat
    "nb_liens_reseau",    # entier : nb de liens sociaux
    "partage_telephone",  # binaire : 0 ou 1
    "age_premier_achat",  # float  : années depuis le premier achat
]
N_FEATURES = len(FEATURE_NAMES)

# ============================================================
# SECTION 2 : Dataset
# ============================================================

class FoncierDataset(Dataset):
    def __init__(self, data: pd.DataFrame, label_col: str = "label"):
        self.features = torch.tensor(data[FEATURE_NAMES].values, dtype=torch.float32)
        if label_col in data.columns:
            label_map = {c: i for i, c in enumerate(CLASSES)}
            self.labels = torch.tensor(data[label_col].map(label_map).values, dtype=torch.long)
        else:
            self.labels = None

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        if self.labels is not None:
            return self.features[idx], self.labels[idx]
        return self.features[idx]

    @staticmethod
    def from_csv(path: str) -> "FoncierDataset":
        return FoncierDataset(pd.read_csv(path))


# ============================================================
# SECTION 3 : Architecture réseau
# ============================================================

class FraudDetectorNet(nn.Module):
    """
    MLP 3 couches pour la classification de fraude foncière.

    Input(6) -> BN -> Dense(64) -> ReLU -> Dropout(0.3)
             -> Dense(128) -> ReLU -> Dropout(0.3)
             -> Dense(64)  -> ReLU -> Dropout(0.2)
             -> Dense(4)   -> Softmax
    """

    def __init__(self, n_features=N_FEATURES, n_classes=N_CLASSES,
                 hidden_sizes=[64, 128, 64], dropout_rates=[0.3, 0.3, 0.2]):
        super().__init__()
        self.n_features = n_features
        self.n_classes  = n_classes
        self.input_bn   = nn.BatchNorm1d(n_features)

        layers, in_size = [], n_features
        for hidden, drop in zip(hidden_sizes, dropout_rates):
            layers += [nn.Linear(in_size, hidden), nn.BatchNorm1d(hidden),
                       nn.ReLU(), nn.Dropout(drop)]
            in_size = hidden

        self.hidden = nn.Sequential(*layers)
        self.output = nn.Linear(in_size, n_classes)

    def forward(self, x):
        return self.output(self.hidden(self.input_bn(x)))

    def predict_proba(self, x):
        self.eval()
        with torch.no_grad():
            return F.softmax(self.forward(x), dim=-1)

    def predict_class(self, x):
        proba = self.predict_proba(x)
        indices = proba.argmax(dim=-1).tolist()
        if isinstance(indices, int):
            return CLASSES[indices]
        return [CLASSES[i] for i in indices]


# ============================================================
# SECTION 4 : Entraînement
# ============================================================

class FraudTrainer:
    def __init__(self, model, lr=1e-3, weight_decay=1e-4, device=None):
        self.device  = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model   = model.to(self.device)
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(self.optimizer, patience=5, factor=0.5)
        weights = torch.tensor([1.0, 2.0, 3.0, 4.0], device=self.device)
        self.criterion = nn.CrossEntropyLoss(weight=weights)
        self.history = {"train_loss": [], "val_loss": [], "val_acc": []}

    def train_epoch(self, loader):
        self.model.train()
        total = 0.0
        for X, y in loader:
            X, y = X.to(self.device), y.to(self.device)
            self.optimizer.zero_grad()
            loss = self.criterion(self.model(X), y)
            loss.backward()
            nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            total += loss.item() * len(X)
        return total / len(loader.dataset)

    @torch.no_grad()
    def evaluate(self, loader):
        self.model.eval()
        total, correct = 0.0, 0
        for X, y in loader:
            X, y = X.to(self.device), y.to(self.device)
            logits = self.model(X)
            total   += self.criterion(logits, y).item() * len(X)
            correct += (logits.argmax(1) == y).sum().item()
        n = len(loader.dataset)
        return total / n, correct / n

    def fit(self, train_loader, val_loader=None, epochs=100, verbose=True):
        for ep in range(1, epochs + 1):
            tl = self.train_epoch(train_loader)
            self.history["train_loss"].append(tl)
            if val_loader:
                vl, va = self.evaluate(val_loader)
                self.history["val_loss"].append(vl)
                self.history["val_acc"].append(va)
                self.scheduler.step(vl)
                if verbose and ep % 10 == 0:
                    print(f"Epoch {ep:3d} | Train {tl:.4f} | Val {vl:.4f} | Acc {va:.3f}")
            elif verbose and ep % 10 == 0:
                print(f"Epoch {ep:3d} | Train {tl:.4f}")

    def save(self, path):
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "history": self.history,
            "n_features": self.model.n_features,
            "n_classes":  self.model.n_classes,
            "classes":    CLASSES,
            "feature_names": FEATURE_NAMES,
        }, path)
        print(f"Modèle sauvegardé : {path}")


# ============================================================
# SECTION 5 : Chargement
# ============================================================

def load_model(path: str, device=None) -> FraudDetectorNet:
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(path, map_location=device)
    model = FraudDetectorNet(n_features=ckpt["n_features"], n_classes=ckpt["n_classes"])
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    print(f"Modèle chargé : {path}")
    return model


# ============================================================
# SECTION 6 : Données synthétiques
# ============================================================

def generate_synthetic_data(n_samples=200, seed=42) -> pd.DataFrame:
    rng  = np.random.default_rng(seed)
    rows = []

    def r(cls, nb_p, freq, pv, liens, tel, age):
        return dict(nb_parcelles=nb_p, frequence_revente=freq, ratio_plus_value=pv,
                    nb_liens_reseau=liens, partage_telephone=tel, age_premier_achat=age, label=cls)

    n_std = int(n_samples * 0.4)
    n_aty = int(n_samples * 0.2)
    n_spe = int(n_samples * 0.2)
    n_fra = n_samples - n_std - n_aty - n_spe

    for _ in range(n_std):
        rows.append(r("standard",    rng.integers(1,3),  rng.uniform(0,.1),  rng.uniform(-.1,.3), rng.integers(0,2), 0,                         rng.uniform(1,15)))
    for _ in range(n_aty):
        rows.append(r("atypique",    rng.integers(2,4),  rng.uniform(.1,.4), rng.uniform(.3,.5),  rng.integers(1,3), int(rng.random()<.3),       rng.uniform(.5,5)))
    for _ in range(n_spe):
        rows.append(r("speculateur", rng.integers(3,6),  rng.uniform(.4,.8), rng.uniform(.5,1.5), rng.integers(1,4), int(rng.random()<.5),       rng.uniform(.2,3)))
    for _ in range(n_fra):
        rows.append(r("fraude",      rng.integers(4,10), rng.uniform(.5,1.), rng.uniform(.8,3.),  rng.integers(3,8), 1,                          rng.uniform(.1,2)))

    return pd.DataFrame(rows).sample(frac=1, random_state=seed).reset_index(drop=True)


# ============================================================
# SECTION 7 : Inférence acteur (pour main.py)
# ============================================================

def predict_actor(features: dict, model: FraudDetectorNet) -> dict:
    x = torch.tensor([[features[f] for f in FEATURE_NAMES]], dtype=torch.float32)
    proba = model.predict_proba(x).squeeze().tolist()
    classe = CLASSES[int(np.argmax(proba))]
    return {"classe": classe, "probabilites": dict(zip(CLASSES, proba)), "confiance": max(proba)}


# ============================================================
# Entraînement principal
# ============================================================

def train_and_save(dataset_path="dataset.csv", output_path="model_weights.pth",
                   epochs=100, batch_size=16, val_split=0.2):
    print("=== LandGuard — Entraînement neuronal ===\n")
    if Path(dataset_path).exists():
        df = pd.read_csv(dataset_path)
        print(f"Dataset : {len(df)} dossiers")
    else:
        print("Génération données synthétiques...")
        df = generate_synthetic_data(200)

    for col in ["nb_parcelles","frequence_revente","ratio_plus_value","nb_liens_reseau","age_premier_achat"]:
        m, s = df[col].mean(), df[col].std()
        df[col] = (df[col] - m) / (s + 1e-8)

    split = int(len(df) * (1 - val_split))
    train_ds = FoncierDataset(df.iloc[:split])
    val_ds   = FoncierDataset(df.iloc[split:])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=batch_size)

    model   = FraudDetectorNet()
    trainer = FraudTrainer(model)
    trainer.fit(train_loader, val_loader, epochs=epochs)
    trainer.save(output_path)
    _, acc = trainer.evaluate(val_loader)
    print(f"\nPrécision validation finale : {acc:.3f}")
    return model, trainer


if __name__ == "__main__":
    train_and_save()
