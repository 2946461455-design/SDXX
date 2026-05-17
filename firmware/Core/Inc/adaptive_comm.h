#ifndef ADAPTIVE_COMM_H
#define ADAPTIVE_COMM_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define ADC_WINDOW_SIZE              (256U)
#define ADC_SAMPLE_MAX               (4095.0f)
#define FEATURE_VECTOR_SIZE          (12U)
#define FRAME_PAYLOAD_SIZE           (16U)
#define PREAMBLE_WORD                (0xA55AA55AU)

typedef enum {
    MOD_OOK = 0,
    MOD_2PPM = 1,
    MOD_4PPM = 2,
    MOD_2PAM = 3,
    MOD_4PAM = 4
} modulation_t;

typedef enum {
    RATE_1M = 0,
    RATE_2M = 1,
    RATE_5M = 2
} symbol_rate_t;

typedef struct {
    float mean;
    float variance;
    float peak_to_peak;
    float dominant_energy;
    float bandwidth_idx;
    float snr_db;
    float ber_est;
    float scint_idx;
    float pulse_width_us;
    float temperature_c;
    float turbidity_ntu;
    float battery_v;
} channel_features_t;

typedef struct {
    uint8_t quality_level;      // 0~3
    modulation_t modulation;
    symbol_rate_t symbol_rate;
    uint8_t tx_power_level;     // 0~15
    uint8_t pga_gain_level;     // 0~7
    float threshold;
} control_action_t;

typedef struct {
    uint16_t src;
    uint16_t dst;
    uint8_t frame_type;
    uint8_t seq;
    uint16_t ctrl;
    uint8_t payload[FRAME_PAYLOAD_SIZE];
    uint32_t crc32;
} phy_frame_t;

void adaptive_comm_init(void);
void adaptive_comm_set_env(float temperature_c, float turbidity_ntu, float battery_v);
void adaptive_comm_on_samples(const uint16_t *samples, uint16_t n);
void adaptive_comm_build_features(channel_features_t *f);
void adaptive_comm_infer(const channel_features_t *f, control_action_t *a);
void adaptive_comm_apply(const control_action_t *a);

bool adaptive_comm_build_frame(uint16_t src, uint16_t dst, uint8_t type, uint8_t seq,
                               const uint8_t *payload, uint16_t payload_len,
                               phy_frame_t *out);
bool adaptive_comm_validate_frame(const phy_frame_t *frame);

#ifdef __cplusplus
}
#endif

#endif
