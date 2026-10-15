#pragma once

namespace lumineze_topology {

// Engine-owned settings; never instantiated in schedule firmware.
struct SeasonalSettings {
  float latitude = -28.5f;
  float noon_minutes = 750.0f;
  float phase_days = 182.6f;
  float visible_winter = 0.75f;
  float visible_summer = 1.0f;
  float visible_exponent = 1.0f;
  float uv_start_minutes = 90.0f;
  float uv_end_minutes = 90.0f;
  float uv_winter = 0.8f;
  float uv_summer = 1.0f;
  float uv_exponent = 1.0f;
};

}  // namespace lumineze_topology
