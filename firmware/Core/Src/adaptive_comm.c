#include "../Inc/adaptive_comm.h"
#include "../../ai/tiny_model.h"
#include <string.h>

#define SAMPLE_BUF_SZ 2048U

static uint16_t g_samples[SAMPLE_BUF_SZ];
static uint16_t g_n;
static float g_temperature = 24.0f;
static float g_turbidity = 1.0f;
static float g_battery = 3.7f;

static uint32_t crc32_sw(const uint8_t *data, uint16_t len) {
    uint32_t crc = 0xFFFFFFFFu;
    for (uint16_t i = 0; i < len; ++i) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; ++j) {
            crc = (crc >> 1) ^ (0xEDB88320u & (uint32_t)(-(int32_t)(crc & 1u)));
        }
    }
    return ~crc;
}

static void hw_set_tx_power(uint8_t level) { (void)level; }
static void hw_set_modulation(modulation_t m, symbol_rate_t r) { (void)m; (void)r; }
static void hw_set_rx_threshold(float t) { (void)t; }
static void hw_set_pga_gain(uint8_t l) { (void)l; }

void adaptive_comm_init(void) { memset(g_samples, 0, sizeof(g_samples)); g_n = 0; }
void adaptive_comm_set_env(float temperature_c, float turbidity_ntu, float battery_v) { g_temperature = temperature_c; g_turbidity = turbidity_ntu; g_battery = battery_v; }
void adaptive_comm_on_samples(const uint16_t *samples, uint16_t n) {
    if (n > SAMPLE_BUF_SZ) n = SAMPLE_BUF_SZ;
    memcpy(g_samples, samples, n * sizeof(uint16_t)); g_n = n;
}

void adaptive_comm_build_features(channel_features_t *f) {
    memset(f, 0, sizeof(*f));
    if (g_n == 0) return;

    float minv = 4095.0f, maxv = 0.0f, mean = 0.0f;
    for (uint16_t i = 0; i < g_n; ++i) {
        float v = (float)g_samples[i];
        mean += v; if (v < minv) minv = v; if (v > maxv) maxv = v;
    }
    mean /= (float)g_n;

    float var = 0.0f;
    for (uint16_t i = 0; i < g_n; ++i) {
        float d = (float)g_samples[i] - mean; var += d * d;
    }
    var /= (float)g_n;

    float noise = var * 0.25f + 1.0f;
    float signal = var * 0.75f + 1.0f;
    float snr_lin = signal / noise;

    f->mean = mean / ADC_SAMPLE_MAX;
    f->variance = var / (ADC_SAMPLE_MAX * ADC_SAMPLE_MAX);
    f->peak_to_peak = (maxv - minv) / ADC_SAMPLE_MAX;
    f->dominant_energy = signal / (signal + noise);
    f->bandwidth_idx = f->peak_to_peak * 0.5f + f->variance * 20.0f;
    f->snr_db = 10.0f * snr_lin;
    f->ber_est = (f->snr_db < 8.0f) ? 1e-2f : ((f->snr_db < 14.0f) ? 1e-3f : 1e-4f);
    f->scint_idx = var / (mean * mean + 1e-3f);
    f->pulse_width_us = 1.2f + 6.0f * f->scint_idx;
    f->temperature_c = g_temperature;
    f->turbidity_ntu = g_turbidity;
    f->battery_v = g_battery;
}

void adaptive_comm_infer(const channel_features_t *f, control_action_t *a) { tiny_model_predict(f, a); }
void adaptive_comm_apply(const control_action_t *a) {
    hw_set_tx_power(a->tx_power_level); hw_set_modulation(a->modulation, a->symbol_rate);
    hw_set_pga_gain(a->pga_gain_level); hw_set_rx_threshold(a->threshold);
}

bool adaptive_comm_build_frame(uint16_t src, uint16_t dst, uint8_t type, uint8_t seq,
                               const uint8_t *payload, uint16_t payload_len, phy_frame_t *out) {
    if (!out || !payload || payload_len > FRAME_PAYLOAD_SIZE) return false;
    memset(out, 0, sizeof(*out)); out->src = src; out->dst = dst; out->frame_type = type; out->seq = seq;
    memcpy(out->payload, payload, payload_len);
    out->crc32 = crc32_sw((const uint8_t *)out, (uint16_t)(sizeof(*out) - sizeof(out->crc32)));
    return true;
}

bool adaptive_comm_validate_frame(const phy_frame_t *frame) {
    if (!frame) return false;
    uint32_t calc = crc32_sw((const uint8_t *)frame, (uint16_t)(sizeof(*frame) - sizeof(frame->crc32)));
    return calc == frame->crc32;
}
