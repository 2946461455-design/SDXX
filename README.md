# SDXX - STM32F4智能自适应水下激光通信节点

## 优化后的实现说明
本版在原MVP上完成工程化增强：
- 补齐了**物理层帧结构+CRC校验**。
- 扩展了**信道特征维度**（时域/统计/环境/能量）。
- 实现了**质量分级→调制/速率/功率/PGA增益**联合决策。
- 保持轻量化，可直接迁移到 STM32F4 + FreeRTOS + HAL。

## 代码结构
- `firmware/Core/Inc/adaptive_comm.h`：系统核心类型与API
- `firmware/Core/Src/adaptive_comm.c`：特征提取、执行控制、帧打包与CRC
- `firmware/ai/tiny_model.c`：轻量AI策略（分级+阈值回归）
- `firmware/Core/Src/main_demo.c`：端到端演示
- `scripts/train_policy.py`：离线策略训练脚本

## 你可以如何继续落地
1. 用 DMA 双缓冲把 `adaptive_comm_on_samples()` 接到 ADC ISR 数据流。
2. 在 10~20ms 周期任务调用 `build_features -> infer -> apply`。
3. 将 `hw_set_*` 占位函数替换为 HRTIM/DAC/PGA 实际驱动。
4. 用真实水槽数据替换 `train_policy.py` 合成数据，导出新规则参数。
