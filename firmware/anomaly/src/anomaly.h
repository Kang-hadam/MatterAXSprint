/*
 * Recognise-then-judge temperature anomaly detector for a 1 Hz stream, nRF Edge AI style API:
 * feed samples one by one, run inference whenever a 60 s window is complete.
 * The first 5 minutes are recognised (level, swing, noise). From then on a daily profile of
 * 96 x 15 min slots is learned, and every minute is judged relative to what was recognised:
 * against the recognised level until its time of day is learned (BASIC), afterwards against the
 * learned profile (FULL). ml/features.py is the bit-exact reference.
 *
 * Shared by firmware/anomaly/selftest (replay of embedded data) and firmware/matter/judge_dk
 * (live readings from the Matter temperature sensor).
 */
#ifndef ANOMALY_H_
#define ANOMALY_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define AD_WINDOW   60   /* samples per window (1 Hz -> 1 min) */
#define AD_RECOG    5    /* windows of recognition (5 min) */
#define AD_SLOTS    96   /* slots of the daily profile */
#define AD_SLOT_SEC 900  /* seconds per slot (15 min) */
#define AD_NMAX     7    /* days averaged before a slot becomes a moving average */
#define AD_MINCNT   8    /* windows a slot needs before it is learned */
#define AD_DAY_WIN  1440 /* windows per day */

enum { AD_LEARNING = 0, AD_BASIC = 1, AD_FULL = 2 };

typedef struct {
	float score;     /* anomaly score, 0 while recognising */
	uint8_t phase;   /* AD_LEARNING, AD_BASIC or AD_FULL */
	uint8_t anomaly; /* score >= threshold of the phase */
} ad_result_t;

typedef struct {
	float x0, sum, sumsq, dsum, dmax, prev; /* current window */
	float ema;                              /* EMA of window means: slow level and trend */
	float L0, Bs, Bm, Ba, rs, rq, swing;    /* recognised level, noise baselines, swing */
	float floor;                            /* smallest day-to-day change a slot tolerates */
	float acc_sum;                          /* window means of the current slot */
	float m[AD_SLOTS], d[AD_SLOTS];         /* daily profile: slot mean, day-to-day spread */
	uint32_t k;                             /* completed windows */
	uint32_t sec;                           /* time of day of the latest sample [s] */
	int16_t cur_slot;
	uint16_t n;                             /* samples in the current window */
	uint8_t acc_cnt, acc_alarm, has_prev;
	uint8_t meta[AD_SLOTS];                 /* days learned (bits 0-3), postponed once (bit 7) */
} ad_state_t;

extern const float ad_thr_basic, ad_thr_full;

void ad_init(ad_state_t *s);

/* Feed one sample; returns 1 when a full window is ready for ad_run_inference(). */
int ad_feed(ad_state_t *s, uint32_t sec_of_day, float temp_c);

/* Judge the completed window and update recognition / daily profile. */
ad_result_t ad_run_inference(ad_state_t *s);

#ifdef __cplusplus
}
#endif

#endif /* ANOMALY_H_ */
