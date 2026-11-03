#include "DistrictHeatingReserveControl.h"
#include <cassert>
#include <cstdio>

using Control = DistrictHeatingReserveControl;

static Control::Inputs normal(uint8_t mode = Control::RESERVE_ONLY) {
	return {mode, true, false, false, true, true, true, true, true,
		500, 550, 300, 800, 350, 5, 10};
}

static void advance(Control& control, const Control::Inputs& in, unsigned seconds) {
	while (seconds--) control.tick(in);
}

static void start_reserve(Control& control, Control::Inputs& in) {
	in.city_supply = 250;
	control.tick(in);
	assert(control.get_state() == Control::ISOLATING);
	assert(!control.reserve_requested());
	advance(control, in, in.valve_running_seconds - 1);
	assert(!control.reserve_requested());
	control.tick(in);
	assert(control.get_state() == Control::RESERVE);
	assert(control.city_isolated());
}

int main() {
	{
		Control c;
		auto in = normal();
		advance(c, in, 7200);
		assert(c.get_state() == Control::CITY);
		in.house_supply = 400;
		advance(c, in, in.start_delay_seconds - 1);
		assert(c.get_state() == Control::CITY);
		c.tick(in);
		assert(c.get_state() == Control::ISOLATING);
	}
	{
		Control c;
		auto in = normal(Control::SUPPLEMENT_AND_RESERVE);
		in.house_supply = 400;
		advance(c, in, in.start_delay_seconds);
		assert(c.get_state() == Control::SUPPLEMENT);
		assert(c.reserve_requested() && !c.city_isolated());
		in.house_supply = 550;
		advance(c, in, Control::SUPPLEMENT_OFF_DELAY_SECONDS - 1);
		assert(c.reserve_requested());
		c.tick(in);
		assert(c.get_state() == Control::CITY);
	}
	{
		Control c;
		auto in = normal();
		start_reserve(c, in);
		in.city_supply = 800; // Stagnant sensor alone must not release reserve.
		advance(c, in, Control::PROBE_INTERVAL_SECONDS - 1);
		assert(c.city_isolated() && c.reserve_requested());
		c.tick(in);
		assert(c.probing() && c.reserve_requested());
		advance(c, in, in.valve_running_seconds + Control::PROBE_FLUSH_SECONDS - 1);
		assert(c.probing());
		advance(c, in, Control::RECOVERY_CONFIRM_SECONDS - 1);
		assert(c.probing());
		c.tick(in);
		assert(c.get_state() == Control::CITY && !c.reserve_requested());
	}
	{
		Control c;
		auto in = normal();
		start_reserve(c, in);
		advance(c, in, Control::PROBE_INTERVAL_SECONDS);
		assert(c.probing());
		advance(c, in, in.valve_running_seconds + Control::PROBE_FLUSH_SECONDS + Control::RECOVERY_CONFIRM_SECONDS);
		assert(c.get_state() == Control::ISOLATING);
	}
	{
		Control c;
		auto in = normal();
		in.city_alarm = true;
		c.tick(in);
		advance(c, in, in.valve_running_seconds + 7200);
		assert(c.get_state() == Control::RESERVE); // No probes during city alarm.
		in.system_failure = true;
		c.tick(in);
		assert(!c.reserve_requested());
	}
	{
		Control c;
		auto in = normal();
		start_reserve(c, in);
		in.demand = false;
		c.tick(in);
		assert(!c.reserve_requested());
		in.demand = true;
		start_reserve(c, in);
		in.mode = Control::COMPATIBILITY;
		c.tick(in);
		assert(!c.reserve_requested());
	}
	{
		Control c;
		auto in = normal();
		in.valve_mapped = false;
		in.city_supply_valid = false;
		advance(c, in, 7200);
		assert(c.city_isolated() && !c.reserve_requested());
	}
	{
		Control c;
		auto in = normal(Control::SUPPLEMENT_AND_RESERVE);
		in.house_supply = 400;
		advance(c, in, in.start_delay_seconds);
		in.city_alarm = true;
		c.tick(in);
		assert(c.get_state() == Control::ISOLATING);
	}
	{
		Control c;
		auto in = normal();
		in.house_supply = in.required - Control::START_DELTA;
		advance(c, in, 20);
		assert(c.get_state() == Control::CITY); // Strict lower boundary.
		in.house_supply_valid = false;
		advance(c, in, in.start_delay_seconds);
		assert(c.city_isolated());
	}
	{
		Control c;
		auto in = normal();
		in.start_delay_seconds = 0;
		in.house_supply = 400;
		c.tick(in);
		assert(c.city_isolated());
		in.mode = 255;
		c.tick(in);
		assert(!c.reserve_requested());
	}
	{
		Control c;
		auto in = normal();
		start_reserve(c, in);
		advance(c, in, Control::PROBE_INTERVAL_SECONDS);
		in.city_supply = 800;
		advance(c, in, in.valve_running_seconds + Control::PROBE_FLUSH_SECONDS + 20);
		assert(c.probing());
		in.city_supply_valid = false;
		c.tick(in); // A single invalid observation breaks continuous confirmation.
		in.city_supply_valid = true;
		advance(c, in, Control::RECOVERY_CONFIRM_SECONDS - 21);
		assert(c.get_state() == Control::ISOLATING);
	}
	for (uint8_t mode = Control::RESERVE_ONLY; mode <= Control::SUPPLEMENT_AND_RESERVE; ++mode) {
		Control c;
		auto in = normal(mode);
		start_reserve(c, in);
		advance(c, in, Control::PROBE_INTERVAL_SECONDS);
		in.city_supply = 450; // Useful against 30 C return, insufficient for 50 C target.
		advance(c, in, in.valve_running_seconds + Control::PROBE_FLUSH_SECONDS + Control::RECOVERY_CONFIRM_SECONDS);
		assert(c.get_state() == (mode == Control::RESERVE_ONLY ? Control::ISOLATING : Control::SUPPLEMENT));
	}
	{
		Control c;
		auto in = normal();
		start_reserve(c, in);
		in.mode = Control::SUPPLEMENT_AND_RESERVE;
		in.city_supply = 800;
		in.house_supply = 400;
		c.tick(in);
		assert(c.get_state() == Control::CITY);
		advance(c, in, in.start_delay_seconds - 1);
		assert(c.get_state() == Control::SUPPLEMENT);
	}
	for (int sensor = 0; sensor < 3; ++sensor) {
		Control c;
		auto in = normal();
		if (sensor == 0) in.city_supply_valid = false;
		if (sensor == 1) in.city_return_valid = false;
		if (sensor == 2) in.house_return_valid = false;
		c.tick(in);
		assert(c.city_isolated() && !c.reserve_requested());
	}
	std::puts("District heating reserve transitions: OK");
}