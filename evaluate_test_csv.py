import argparse
from pathlib import Path

import pandas as pd
import numpy as np
from PIL import Image
import tensorflow as tf

from labels import CLASS_NAMES


IMG_SIZE = (48, 48)


def load_image(path: Path):
    img = Image.open(path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr


def main():
    parser = argparse.ArgumentParser(description="在 GTSRB 测试 CSV 上评估模型")
    parser.add_argument("--model", default="gtsrb_cnn.keras", help="模型文件路径")
    parser.add_argument("--test_csv", required=True, help="测试 CSV 路径（含 Path, ClassId 列）")
    parser.add_argument("--base_dir", required=True, help="CSV 中 Path 的根目录")
    parser.add_argument("--show_errors", type=int, default=10, help="打印前 N 个错分样本")
    args = parser.parse_args()

    model = tf.keras.models.load_model(args.model)
    df = pd.read_csv(args.test_csv)

    if "Path" not in df.columns or "ClassId" not in df.columns:
        raise ValueError("CSV 必须包含 Path 和 ClassId 列")

    base_dir = Path(args.base_dir)

    y_true = []
    y_pred = []
    errors = []

    for i, row in df.iterrows():
        image_path = base_dir / row["Path"]
        true_id = int(row["ClassId"])

        x = np.expand_dims(load_image(image_path), axis=0)
        pred_probs = model.predict(x, verbose=0)[0]
        pred_id = int(np.argmax(pred_probs))

        y_true.append(true_id)
        y_pred.append(pred_id)

        if pred_id != true_id and len(errors) < args.show_errors:
            errors.append((str(image_path), true_id, pred_id, float(pred_probs[pred_id])))

        if (i + 1) % 1000 == 0:
            print(f"已评估 {i+1}/{len(df)} 张")

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    accuracy = (y_true == y_pred).mean()

    print(f"\n测试集准确率: {accuracy:.4f} ({(y_true == y_pred).sum()}/{len(y_true)})")

    if errors:
        print("\n错分样本示例:")
        for p, t, pr, conf in errors:
            print(f"Path={p}, True={t}({CLASS_NAMES[t]}), Pred={pr}({CLASS_NAMES[pr]}), Conf={conf:.4f}")


if __name__ == "__main__":
    main()
