## Acknowledgements and provenance

Development of this project was informed by publicly available work documenting and implementing control of Arcadia LuminIZE devices.

In particular:

- Jefrim Keijzer's [article](https://www.jefrim.nl/posts/integration-arcadia-lumenize-with-esphome), *Integrating Arcadia Lumenize ProT5 Lamps with ESPHome and Home Assistant*, provided an example ESPHome configuration and was used as a reference during development of the initial BLE control implementation.
- Amy Kincaid's `[ha-arcadia-lumenize](https://github.com/AmyKincaid/ha-arcadia-lumenize)` Home Assistant integration provided additional reference material when implementing status/readback support.

These sources helped establish how the LuminIZE devices communicate over Bluetooth Low Energy, including relevant service/characteristic UUIDs, command and status packet formats, and observed device behaviour.

The controller architecture, transaction handling, retry and recovery behaviour, scheduling/seasonal control, diagnostics, safety logic, and ESPHome packaging in this repository have subsequently been developed specifically for this project.

Amy Kincaid's `ha-arcadia-lumenize` project is licensed under the Apache License 2.0. See that project for its applicable licence terms.

This project is an independent, unofficial project and is not affiliated with or endorsed by Arcadia Reptile.