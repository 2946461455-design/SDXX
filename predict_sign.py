import argparse

import numpy as np
from PIL import Image
import tensorflow as tf

from labels import CLASS_NAMES


IMG_SIZE = (32, 32)


def preprocess_image(image_path: str):
    img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def main():
    parser = argparse.ArgumentParser(description="使用训练好的模型识别单张交通标志")
    parser.add_argument("--model", type=str, default="gtsrb_cnn.keras", help="模型路径")
    parser.add_argument("--image", type=str, required=True, help="待识别图片路径")
    args = parser.parse_args()

    model = tf.keras.models.load_model(args.model)
    x = preprocess_image(args.image)

    pred = model.predict(x, verbose=0)[0]
    class_id = int(np.argmax(pred))
    confidence = float(pred[class_id])

    print(f"预测类别编号: {class_id}")
    print(f"预测类别名称: {CLASS_NAMES[class_id]}")
    print(f"置信度: {confidence:.4f}")


if __name__ == "__main__":
    main()
