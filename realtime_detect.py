import argparse

import cv2
import numpy as np
import tensorflow as tf

from labels import CLASS_NAMES


IMG_SIZE = (32, 32)


def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """把摄像头帧转换为模型输入格式。"""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, IMG_SIZE)
    arr = resized.astype(np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def main():
    parser = argparse.ArgumentParser(description="摄像头实时交通标志识别")
    parser.add_argument("--model", default="gtsrb_cnn.keras", help="训练好的模型路径")
    parser.add_argument("--camera", type=int, default=0, help="摄像头编号，默认 0")
    parser.add_argument("--threshold", type=float, default=0.60, help="最低置信度阈值")
    args = parser.parse_args()

    model = tf.keras.models.load_model(args.model)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise RuntimeError("无法打开摄像头，请检查设备或修改 --camera 参数")

    print("按 q 退出实时识别")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("读取摄像头画面失败")
            break

        x = preprocess_frame(frame)
        pred = model.predict(x, verbose=0)[0]
        class_id = int(np.argmax(pred))
        confidence = float(pred[class_id])

        if confidence >= args.threshold:
            text = f"{class_id} {CLASS_NAMES[class_id]} ({confidence:.2f})"
            color = (0, 255, 0)
        else:
            text = f"Uncertain ({confidence:.2f})"
            color = (0, 165, 255)

        cv2.putText(
            frame,
            text,
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2,
            cv2.LINE_AA,
        )

        cv2.imshow("GTSRB Realtime Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
