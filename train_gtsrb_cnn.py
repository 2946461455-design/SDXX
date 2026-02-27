import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras import layers, models

from labels import CLASS_NAMES


IMG_SIZE = (32, 32)
NUM_CLASSES = 43


def load_dataset(data_dir: Path):
    """从 GTSRB-Training 目录加载图片和标签。"""
    images = []
    labels = []

    for class_id in range(NUM_CLASSES):
        class_dir = data_dir / f"{class_id:05d}"
        if not class_dir.exists():
            continue

        for image_path in class_dir.glob("*.ppm"):
            img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
            images.append(np.array(img))
            labels.append(class_id)

    x = np.array(images, dtype=np.float32) / 255.0
    y = np.array(labels, dtype=np.int32)
    return x, y


def build_model(input_shape=(32, 32, 3), num_classes=43):
    """一个简单 CNN，适合初学者理解。"""
    model = models.Sequential(
        [
            layers.Input(shape=input_shape),
            layers.Conv2D(32, (3, 3), activation="relu"),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(64, (3, 3), activation="relu"),
            layers.MaxPooling2D((2, 2)),
            layers.Conv2D(128, (3, 3), activation="relu"),
            layers.Flatten(),
            layers.Dense(128, activation="relu"),
            layers.Dropout(0.3),
            layers.Dense(num_classes, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    parser = argparse.ArgumentParser(description="训练 GTSRB 交通标志识别 CNN")
    parser.add_argument(
        "--data_dir",
        type=str,
        required=True,
        help="GTSRB-Training 目录路径（内部应有 00000~00042 子目录）",
    )
    parser.add_argument("--epochs", type=int, default=10, help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=64, help="批大小")
    parser.add_argument(
        "--model_out",
        type=str,
        default="gtsrb_cnn.keras",
        help="模型保存路径",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    x, y = load_dataset(data_dir)
    print(f"加载完成: {len(x)} 张图片")

    x_train, x_val, y_train, y_val = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = build_model()
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=3, restore_best_weights=True
        )
    ]

    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
    )

    loss, acc = model.evaluate(x_val, y_val, verbose=0)
    print(f"验证集准确率: {acc:.4f}")

    model.save(args.model_out)
    print(f"模型已保存到: {args.model_out}")
    print("类别示例:")
    for i in range(5):
        print(f"{i}: {CLASS_NAMES[i]}")


if __name__ == "__main__":
    main()
