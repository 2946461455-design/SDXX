"""
离线训练示例：根据链路特征选择动作（功率/速率/调制）。
可用于后续导出更精细的规则或小模型权重。
"""

from dataclasses import dataclass
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


@dataclass
class Dataset:
    X: np.ndarray
    y_power: np.ndarray
    y_rate: np.ndarray
    y_mod: np.ndarray


def synthesize(n=4000, seed=7) -> Dataset:
    rng = np.random.default_rng(seed)

    snr = rng.uniform(2, 25, n)
    ber = np.clip(10 ** (-snr / 8) + rng.normal(0, 2e-4, n), 1e-5, 5e-2)
    scint = np.clip(rng.normal(0.12, 0.08, n), 0.01, 0.6)
    battery = rng.uniform(3.1, 4.2, n)
    pulse_w = 1.8 + 5.0 * scint + rng.normal(0, 0.2, n)

    X = np.column_stack([snr, ber, scint, battery, pulse_w])

    y_power = np.where((snr < 8) | (ber > 1e-2), 2, np.where(snr > 15, 0, 1))
    y_rate = np.where((snr > 12) & (ber < 5e-4) & (battery > 3.4), 1, 0)
    y_mod = np.where((snr < 10) | (scint > 0.22), 1, 0)  # 1=PPM, 0=OOK

    y_power = np.where(battery < 3.3, np.minimum(y_power, 1), y_power)

    return Dataset(X, y_power, y_rate, y_mod)


def fit_and_report(X, y, name: str):
    xtr, xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=20, random_state=42)
    clf.fit(xtr, ytr)
    pred = clf.predict(xte)
    print(f"\n=== {name} ===")
    print(classification_report(yte, pred, digits=4))
    return clf


def main():
    ds = synthesize()
    fit_and_report(ds.X, ds.y_power, "Power Level")
    fit_and_report(ds.X, ds.y_rate, "Rate Level")
    fit_and_report(ds.X, ds.y_mod, "Modulation")


if __name__ == "__main__":
    main()
