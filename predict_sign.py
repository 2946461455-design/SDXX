import argparse
from pathlib import Path

import numpy as np
from PIL import Image
import tensorflow as tf

from labels import CLASS_NAMES


IMG_SIZE = (48, 48)


def preprocess_image(image_path: Path):
    image = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(image, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def main():
    parser = argparse.ArgumentParser(description="单张交通标志识别")
    parser.add_argument("--model", default="gtsrb_cnn.keras", help="模型文件路径")
    parser.add_argument("--image", required=True, help="测试图片路径")
    parser.add_argument("--topk", type=int, default=3, help="输出前 K 个结果")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(f"未找到图片: {image_path}")

    model = tf.keras.models.load_model(args.model)
    probs = model.predict(preprocess_image(image_path), verbose=0)[0]

    topk_idx = np.argsort(probs)[::-1][: args.topk]

    print(f"输入图片: {image_path}")
    print("Top-K 预测结果:")
    for rank, idx in enumerate(topk_idx, start=1):
        print(f"{rank}. ClassId={idx:02d}, Name={CLASS_NAMES[idx]}, Confidence={probs[idx]:.4f}")


if __name__ == "__main__":
    main()
