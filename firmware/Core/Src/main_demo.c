#include "../Inc/adaptive_comm.h"
#include <stdio.h>

int main(void) {
    adaptive_comm_init();
    adaptive_comm_set_env(18.5f, 6.2f, 3.45f);

    uint16_t samples[ADC_WINDOW_SIZE];
    for (uint16_t i = 0; i < ADC_WINDOW_SIZE; ++i) {
        samples[i] = (i % 16 < 8) ? (uint16_t)(1200 + (i % 7) * 60) : (uint16_t)(800 + (i % 5) * 50);
    }

    channel_features_t f; control_action_t a;
    adaptive_comm_on_samples(samples, ADC_WINDOW_SIZE);
    adaptive_comm_build_features(&f);
    adaptive_comm_infer(&f, &a);
    adaptive_comm_apply(&a);

    uint8_t payload[FRAME_PAYLOAD_SIZE] = {1,2,3,4};
    phy_frame_t frame;
    adaptive_comm_build_frame(0x1001, 0x1002, 0x01, 0x10, payload, 4, &frame);

    printf("Q=%u SNR=%.2f BER=%g MOD=%u RATE=%u PWR=%u PGA=%u THR=%.3f FRAME_OK=%d\n",
           a.quality_level, f.snr_db, f.ber_est, a.modulation, a.symbol_rate,
           a.tx_power_level, a.pga_gain_level, a.threshold, adaptive_comm_validate_frame(&frame));
    return 0;
}
