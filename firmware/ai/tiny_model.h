#ifndef TINY_MODEL_H
#define TINY_MODEL_H

#include <stdint.h>
#include "../Core/Inc/adaptive_comm.h"

#ifdef __cplusplus
extern "C" {
#endif

// 轻量模型：逻辑回归 + 规则融合（可替换为X-CUBE-AI导出的模型）
void tiny_model_predict(const channel_features_t *f, control_action_t *a);

#ifdef __cplusplus
}
#endif

#endif // TINY_MODEL_H
