/*
 * nRF54LM20-DK: recognise-then-judge temperature anomaly detection (PyTorch-trained, plain C runtime).
 * Replays three embedded 3-day deployments (room 20 C, sauna 50 C, freezer -18 C) through ONE model as
 * if they were live sensors: prints the recognition, phase changes and alarms, checks every score
 * against the Python reference (FNV-1a hash of all score bits) and times the detector with the GRTC
 * (the DWT cycle counter does not run on nRF54L once the debugger has detached).
 */
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>

#include "anomaly.h"
#include "test_data.h"

static ad_state_t st; /* recognition + 96-slot daily profile */

static void print_when(uint32_t i, uint32_t sec)
{
	printk("D%u %02u:%02u", i / 86400u + 1, sec / 3600u, sec / 60u % 60u);
}

static uint32_t fnv1a(uint32_t h, float f)
{
	uint32_t u;

	memcpy(&u, &f, sizeof(u));
	for (int b = 0; b < 4; b++) {
		h = (h ^ ((u >> (8 * b)) & 0xFFu)) * 16777619u;
	}
	return h;
}

static bool replay(int sc)
{
	uint32_t tp = 0, fp = 0, tn = 0, fn = 0, n_basic = 0, n_full = 0, runs = 0, w = 0;
	uint32_t hash = 2166136261u, alarm_from = 0;
	bool basic_seen = false, full_seen = false, alarm = false;
	float peak = 0.0f;

	ad_init(&st);
	printk("\n=== %s: sensor installed at %02u:%02u, %u days at 1 Hz ===\n", test_name[sc],
	       test_start_sec[sc] / 3600u, test_start_sec[sc] / 60u % 60u, TEST_N_SAMPLES / 86400u);

	for (uint32_t i = 0; i < TEST_N_SAMPLES; i++) {
		const uint32_t sec = (test_start_sec[sc] + i) % 86400u;
		const float temp = test_temp_centi[sc][i] / 100.0f;

		if (!ad_feed(&st, sec, temp)) {
			continue;
		}
		const ad_result_t r = ad_run_inference(&st);
		const bool truth = test_label[sc][w++] != 0;

		if (r.phase == AD_LEARNING) {
			continue;
		}
		if (r.phase == AD_BASIC && !basic_seen) {
			print_when(i, sec);
			printk("  recognised %.2f C (swing %.2f) -> BASIC: judged against the recognised level\n",
			       (double)st.L0, (double)(st.swing));
			basic_seen = true;
		}
		if (r.phase == AD_FULL && !full_seen) {
			print_when(i, sec);
			printk("  daily profile learned -> FULL: judged against the time-of-day profile\n");
			full_seen = true;
		}
		hash = fnv1a(hash, r.score);
		n_basic += r.phase == AD_BASIC;
		n_full += r.phase == AD_FULL;
		tp += r.anomaly && truth;
		fp += r.anomaly && !truth;
		tn += !r.anomaly && !truth;
		fn += !r.anomaly && truth;

		if (r.anomaly && !alarm) {
			print_when(i, sec);
			printk("  ANOMALY  score=%.1f  temp=%.2f C  [%s]\n", (double)r.score, (double)temp,
			       r.phase == AD_FULL ? "FULL" : "BASIC");
			peak = r.score;
			alarm_from = i;
			runs++;
		} else if (r.anomaly) {
			peak = r.score > peak ? r.score : peak;
		} else if (alarm) {
			print_when(i, sec);
			printk("  normal   (peak score %.1f, %u min)\n", (double)peak, (i - alarm_from) / 60u);
		}
		alarm = r.anomaly;
	}

	const uint32_t n = tp + fp + tn + fn;
	const bool match = tp == test_expect[sc][0] && fp == test_expect[sc][1] &&
			   tn == test_expect[sc][2] && fn == test_expect[sc][3] && hash == test_expect[sc][4];

	printk("--- %s: %u windows judged (BASIC %u, FULL %u), %u alarms\n", test_name[sc], n, n_basic,
	       n_full, runs);
	printk("TP=%u FP=%u TN=%u FN=%u  accuracy=%.4f  recall=%.4f  score hash 0x%08X\n", tp, fp, tn, fn,
	       (double)(tp + tn) / n, (double)tp / (tp + fn ? tp + fn : 1), hash);
	printk("matches Python reference (counts + every score bit): %s\n", match ? "YES" : "NO");
	return match;
}

static void benchmark(void)
{
	uint64_t t_inf = 0, t_max = 0, ovh = 0;
	uint32_t calls = 0;
	const unsigned int key = irq_lock();

	ad_init(&st);
	const uint64_t t0 = k_cycle_get_64();

	for (uint32_t i = 0; i < TEST_N_SAMPLES; i++) {
		if (!ad_feed(&st, (test_start_sec[0] + i) % 86400u, test_temp_centi[0][i] / 100.0f)) {
			continue;
		}
		const uint64_t a = k_cycle_get_64();

		(void)ad_run_inference(&st);
		const uint64_t b = k_cycle_get_64() - a;

		t_inf += b;
		t_max = b > t_max ? b : t_max;
		calls++;
	}
	const uint64_t t_all = k_cycle_get_64() - t0;

	for (int j = 0; j < 1000; j++) {
		const uint64_t a = k_cycle_get_64();

		ovh += k_cycle_get_64() - a;
	}
	irq_unlock(key);

	const double ovh_us = (double)k_cyc_to_ns_floor64(ovh) / 1000.0 / 1000.0;
	const double inf_us = (double)k_cyc_to_ns_floor64(t_inf) / 1000.0 / calls - ovh_us;
	const double all_us = (double)k_cyc_to_ns_floor64(t_all) / 1000.0;
	const double feed_us = (all_us - inf_us * calls - 2.0 * ovh_us * calls) / TEST_N_SAMPLES;

	printk("\n--- timing (%s replay, GRTC 1 MHz, interrupts locked) ---\n", test_name[0]);
	printk("inference: avg %.2f us, max %.0f us per 60 s window (%u calls)\n", inf_us,
	       (double)k_cyc_to_ns_floor64(t_max) / 1000.0, calls);
	printk("feed: %.3f us per sample -> one window (60 feeds + inference) %.2f us\n", feed_us,
	       60.0 * feed_us + inf_us);
	printk("CPU load at 1 Hz: %.5f %% | detector state (incl. daily profile): %u B\n",
	       (60.0 * feed_us + inf_us) / 60e6 * 100.0, (unsigned int)sizeof(st));
}

int main(void)
{
	bool all = true;

	printk("\n*** Temperature anomaly detection (recognise, then judge) - nRF54LM20 ***\n");
	printk("one model for every space; thresholds BASIC %.3f / FULL %.3f\n", (double)ad_thr_basic,
	       (double)ad_thr_full);
	for (int sc = 0; sc < TEST_SCENARIOS; sc++) {
		all &= replay(sc);
	}
	printk("\nall deployments match the Python reference: %s\n", all ? "YES" : "NO");
	benchmark();
	return 0;
}
