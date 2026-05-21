# SDXX - GTSRB 交通标志识别（深度学习项目）

按你的新要求，这个项目现在聚焦于：
1. 使用你提供的 `GTSRB-Training` 数据训练模型。
2. 使用你提供的测试文件进行识别，并输出准确率。
3. 也支持对单张测试图片进行预测。

## 1) 环境安装

建议 Python 3.9+：

```bash
pip install tensorflow pillow numpy pandas
```

## 2) 数据准备

### 训练数据
请准备目录：

```text
GTSRB-Training/
  00000/
    *.ppm
  00001/
    *.ppm
  ...
  00042/
    *.ppm
```

### 测试数据（你提供）
常见格式是一个 CSV（含 `Path`, `ClassId`）和图片根目录。

例如：
- `Test.csv`
- `GTSRB/`（里面有 CSV 的 `Path` 对应图片）

## 3) 训练模型

```bash
python train_gtsrb_cnn.py --data_dir /path/to/GTSRB-Training --epochs 20 --batch_size 64 --model_out gtsrb_cnn.keras
```

训练脚本会：
- 自动划分训练/验证集
- 使用数据增强 + CNN
- 使用 EarlyStopping/学习率衰减
- 保存最佳模型 `gtsrb_cnn.keras`

## 4) 测试集评估（你提供测试文件后用这个）

```bash
python evaluate_test_csv.py --model gtsrb_cnn.keras --test_csv /path/to/Test.csv --base_dir /path/to/GTSRB
```

输出：
- 测试集总体准确率
- 错分样本示例（路径、真值、预测值、置信度）

## 5) 单张图片识别

```bash
python predict_sign.py --model gtsrb_cnn.keras --image /path/to/test_image.ppm --topk 3
```

输出：
- Top-K 类别编号、名称、置信度

## 6) 文件说明

- `train_gtsrb_cnn.py`：训练 CNN 模型
- `evaluate_test_csv.py`：测试 CSV 批量评估
- `predict_sign.py`：单图预测
- `labels.py`：GTSRB 的 43 个类别名
