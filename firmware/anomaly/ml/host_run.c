/* Host build of the firmware detector for ml/c_check.py: every window of every embedded scenario. */
#include <stdio.h>
#include <string.h>

#include "anomaly.h"
#include "test_data.h"

int main(void)
{
	static ad_state_t s;

	printf("state %u\n", (unsigned int)sizeof(s));
	for (int sc = 0; sc < TEST_SCENARIOS; sc++) {
		ad_init(&s);
		for (uint32_t i = 0; i < TEST_N_SAMPLES; i++) {
			if (!ad_feed(&s, (test_start_sec[sc] + i) % 86400u, test_temp_centi[sc][i] / 100.0f)) {
				continue;
			}
			ad_result_t r = ad_run_inference(&s);
			uint32_t u;

			memcpy(&u, &r.score, sizeof(u));
			printf("%d %u %08x %u\n", sc, r.phase, u, r.anomaly);
		}
	}
	return 0;
}
