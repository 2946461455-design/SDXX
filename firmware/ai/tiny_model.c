#include "tiny_model.h"

static float clampf(float x, float lo, float hi) {
    if (x < lo) return lo;
    if (x > hi) return hi;
    return x;
}

static uint8_t classify_quality(const channel_features_t *f) {
    if (f->snr_db > 20.0f && f->ber_est < 1e-4f && f->turbidity_ntu < 2.0f) return 0;
    if (f->snr_db > 14.0f && f->ber_est < 5e-4f) return 1;
    if (f->snr_db > 8.0f  && f->ber_est < 2e-3f) return 2;
    return 3;
}

static float predict_delta_threshold(const channel_features_t *f) {
    const float z =
        -0.022f
        - 0.012f * f->snr_db
        + 0.42f * f->scint_idx
        + 0.26f * f->ber_est * 1000.0f
        + 0.03f * f->turbidity_ntu;
    return clampf(z, -0.3f, 0.3f);
}

void tiny_model_predict(const channel_features_t *f, control_action_t *a) {
    a->quality_level = classify_quality(f);
    a->modulation = MOD_OOK;
    a->symbol_rate = RATE_5M;
    a->tx_power_level = 4;
    a->pga_gain_level = 2;

    switch (a->quality_level) {
        case 0:
            a->modulation = MOD_OOK; a->symbol_rate = RATE_5M; a->tx_power_level = 2; a->pga_gain_level = 1; break;
        case 1:
            a->modulation = MOD_2PPM; a->symbol_rate = RATE_2M; a->tx_power_level = 5; a->pga_gain_level = 2; break;
        case 2:
            a->modulation = MOD_4PPM; a->symbol_rate = RATE_2M; a->tx_power_level = 8; a->pga_gain_level = 4; break;
        default:
            a->modulation = MOD_4PPM; a->symbol_rate = RATE_1M; a->tx_power_level = 12; a->pga_gain_level = 6; break;
    }

    if (f->battery_v < 3.35f && a->tx_power_level > 8) {
        a->tx_power_level = 8;
        a->symbol_rate = RATE_1M;
    }

    a->threshold = clampf(0.5f + predict_delta_threshold(f), 0.15f, 0.85f);
}
