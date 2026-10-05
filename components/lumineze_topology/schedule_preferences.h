#pragma once

#include "schedule_store.h"
#include "esphome/core/preferences.h"

namespace lumineze_topology {

// Allocate each platform preference backend once, not once per user action.
class SchedulePreferences {
 public:
  void initialize(uint32_t first_key, uint32_t second_key) {
    if (initialized_) return;
    banks_[0] = esphome::global_preferences->make_preference<ScheduleRecord>(first_key);
    banks_[1] = esphome::global_preferences->make_preference<ScheduleRecord>(second_key);
    initialized_ = true;
  }
  bool read(int bank, ScheduleRecord &record) { return banks_[bank].load(&record); }
  bool write(int bank, const ScheduleRecord &record) { return banks_[bank].save(&record); }
  bool flush() { return esphome::global_preferences->sync(); }

 private:
  std::array<esphome::ESPPreferenceObject, 2> banks_{};
  bool initialized_ = false;
};

}  // namespace lumineze_topology
