/*
 * Thread network settings shared by the sensor (dongle) and the LED board (DK).
 */

#include <errno.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/openthread.h>
#include <openthread/dataset.h>

#include "thread_net.h"

LOG_MODULE_REGISTER(thread_net, LOG_LEVEL_INF);

/*
 * Test credentials only. Both boards must use the same values.
 * Do not use these values in a product.
 */
#define NET_NAME    "TempAlarm"
#define NET_CHANNEL 15
#define NET_PANID   0x7e57

static const uint8_t net_key[OT_NETWORK_KEY_SIZE] = {
	0x4b, 0x1d, 0x90, 0x3a, 0xc7, 0x52, 0xe8, 0x06,
	0x7f, 0xa3, 0x15, 0xd9, 0x6c, 0x28, 0xb4, 0xe1,
};

static const uint8_t net_xpanid[OT_EXT_PAN_ID_SIZE] = {
	0x7e, 0x57, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5, 0xa6,
};

static const uint8_t net_mesh_local_prefix[OT_MESH_LOCAL_PREFIX_SIZE] = {
	0xfd, 0x7e, 0x57, 0xa1, 0xa2, 0xa3, 0xa4, 0x00,
};

int thread_net_start(void)
{
	struct otInstance *ot = openthread_get_default_instance();
	otOperationalDataset dataset;
	otError err;

	memset(&dataset, 0, sizeof(dataset));

	dataset.mActiveTimestamp.mSeconds = 1;
	dataset.mComponents.mIsActiveTimestampPresent = true;

	dataset.mChannel = NET_CHANNEL;
	dataset.mComponents.mIsChannelPresent = true;

	dataset.mPanId = NET_PANID;
	dataset.mComponents.mIsPanIdPresent = true;

	memcpy(dataset.mExtendedPanId.m8, net_xpanid, sizeof(net_xpanid));
	dataset.mComponents.mIsExtendedPanIdPresent = true;

	memcpy(dataset.mNetworkKey.m8, net_key, sizeof(net_key));
	dataset.mComponents.mIsNetworkKeyPresent = true;

	memcpy(dataset.mMeshLocalPrefix.m8, net_mesh_local_prefix,
	       sizeof(net_mesh_local_prefix));
	dataset.mComponents.mIsMeshLocalPrefixPresent = true;

	otNetworkNameFromString(&dataset.mNetworkName, NET_NAME);
	dataset.mComponents.mIsNetworkNamePresent = true;

	/* Replace any network settings that an earlier program stored in flash. */
	openthread_mutex_lock();
	err = otDatasetSetActive(ot, &dataset);
	openthread_mutex_unlock();

	if (err != OT_ERROR_NONE) {
		LOG_ERR("Failed to set the Thread dataset [%d]", err);
		return -EIO;
	}

	return openthread_run();
}
