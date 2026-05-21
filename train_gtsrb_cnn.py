import argparse
from pathlib import Path

import tensorflow as tf
from tensorflow.keras import layers, models


IMG_SIZE = (48, 48)
NUM_CLASSES = 43


def build_datasets(data_dir: Path, batch_size: int, val_split: float, seed: int):
    """从 GTSRB-Training 目录构建训练/验证数据集。"""
    train_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        labels="inferred",
        label_mode="int",
        image_size=IMG_SIZE,
        batch_size=batch_size,
        validation_split=val_split,
        subset="training",
        seed=seed,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        data_dir,
        labels="inferred",
        label_mode="int",
        image_size=IMG_SIZE,
        batch_size=batch_size,
        validation_split=val_split,
        subset="validation",
        seed=seed,
    )

    class_names = train_ds.class_names
    if len(class_names) != NUM_CLASSES:
        print(f"警告：检测到类别数 {len(class_names)}，预期为 {NUM_CLASSES}。")

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.shuffle(1000).prefetch(autotune)
    val_ds = val_ds.prefetch(autotune)
    return train_ds, val_ds


def build_model(num_classes: int = NUM_CLASSES):
    """一个适合初学者的 CNN 网络。"""
    data_augmentation = tf.keras.Sequential(
        [
            layers.RandomRotation(0.06),
            layers.RandomZoom(0.1),
            layers.RandomContrast(0.15),
        ]
    )

    model = models.Sequential(
        [
            layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3)),
            layers.Rescaling(1.0 / 255),
            data_augmentation,
            layers.Conv2D(32, 3, padding="same", activation="relu"),
            layers.BatchNormalization(),
            layers.MaxPooling2D(),
            layers.Conv2D(64, 3, padding="same", activation="relu"),
            layers.BatchNormalization(),
            layers.MaxPooling2D(),
            layers.Conv2D(128, 3, padding="same", activation="relu"),
            layers.BatchNormalization(),
            layers.MaxPooling2D(),
            layers.Dropout(0.25),
            layers.Flatten(),
            layers.Dense(128, activation="relu"),
            layers.Dropout(0.35),
            layers.Dense(num_classes, activation="softmax"),
        ]
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    parser = argparse.ArgumentParser(description="训练 GTSRB 交通标志 CNN 模型")
    parser.add_argument("--data_dir", required=True, help="GTSRB-Training 根目录")
    parser.add_argument("--epochs", type=int, default=20, help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=64, help="批大小")
    parser.add_argument("--val_split", type=float, default=0.2, help="验证集比例")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--model_out", default="gtsrb_cnn.keras", help="模型输出文件")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(f"未找到数据目录: {data_dir}")

    train_ds, val_ds = build_datasets(data_dir, args.batch_size, args.val_split, args.seed)
    model = build_model()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(args.model_out, monitor="val_accuracy", save_best_only=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2),
    ]

    model.fit(train_ds, validation_data=val_ds, epochs=args.epochs, callbacks=callbacks)
    loss, acc = model.evaluate(val_ds, verbose=0)
    print(f"验证集准确率: {acc:.4f}, 验证集损失: {loss:.4f}")
    print(f"最佳模型已保存到: {args.model_out}")


if __name__ == "__main__":
    main()
