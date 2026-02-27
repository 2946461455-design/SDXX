# SDXX - GTSRB 交通标志识别（CNN 入门版）

现在项目支持两种方式：
- 用 `GTSRB-Training` 训练一个 CNN 模型。
- 打开摄像头实时监测交通标志并输出类别。

> 说明：这是初学者版本，先追求简单可运行。

## 1. 环境准备

建议 Python 3.9+。

```bash
pip install tensorflow pillow numpy scikit-learn opencv-python
```

## 2. 数据集目录

解压 `GTSRB-Training` 后目录应类似：

```text
GTSRB-Training/
  00000/
    *.ppm
  ...
  00042/
    *.ppm
```

## 3. 训练模型

```bash
python train_gtsrb_cnn.py --data_dir /path/to/GTSRB-Training --epochs 10 --batch_size 64 --model_out gtsrb_cnn.keras
```

训练后得到 `gtsrb_cnn.keras`。

## 4. 摄像头实时识别

```bash
python realtime_detect.py --model gtsrb_cnn.keras --camera 0 --threshold 0.6
```

- `--camera`：摄像头编号（默认 0）
- `--threshold`：最低置信度阈值（低于阈值会显示 `Uncertain`）
- 按 `q` 键退出

## 5. 单图识别（保留）

```bash
python predict_sign.py --model gtsrb_cnn.keras --image /path/to/one_sign_image.ppm
```

## 6. 文件说明

- `train_gtsrb_cnn.py`：训练脚本
- `realtime_detect.py`：摄像头实时识别脚本
- `predict_sign.py`：单图识别脚本
- `labels.py`：43 类交通标志名称
