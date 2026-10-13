/*
 * Data model callbacks for the alarm endpoint (OnOff server on endpoint 2).
 */

#include "judge.h"

#include <app-common/zap-generated/attributes/Accessors.h>
#include <app-common/zap-generated/ids/Attributes.h>
#include <app-common/zap-generated/ids/Clusters.h>
#include <app/ConcreteAttributePath.h>
#include <lib/support/logging/CHIPLogging.h>

using namespace ::chip;
using namespace ::chip::app::Clusters;

void MatterPostAttributeChangeCallback(const chip::app::ConcreteAttributePath &attributePath, uint8_t type,
				       uint16_t size, uint8_t *value)
{
	if (attributePath.mEndpointId != Judge::kAlarmEndpointId) {
		return;
	}

	if (attributePath.mClusterId == OnOff::Id && attributePath.mAttributeId == OnOff::Attributes::OnOff::Id) {
		ChipLogProgress(Zcl, "Alarm OnOff set to %u", *value);
		Judge::Instance().OnAlarmAttributeWritten(*value != 0);
	}
}

void emberAfOnOffClusterInitCallback(EndpointId endpoint)
{
	bool storedValue;

	if (OnOff::Attributes::OnOff::Get(endpoint, &storedValue) == Protocols::InteractionModel::Status::Success) {
		Judge::Instance().OnAlarmAttributeWritten(storedValue);
	}
}
