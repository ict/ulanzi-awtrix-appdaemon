# Ulanzi TC001 Appdaemon Flows

This is a collection of [Appdaemon](https://appdaemon.readthedocs.io/en/latest/index.html) Apps to drive a [Ulanzi Desktop Clock (TC001)](https://www.ulanzi.com/products/ulanzi-pixel-smart-clock-2882) with the [Awtrix Light](https://github.com/Blueforcer/awtrix-light) firmware.

For any information regarding installing and using Appdaemon with Homeassistant, please consult the documentation.

## Basic configuration of all apps

All apps here make use of a base class to abstract away the Ulanzi protocol and common settings. Therefore some settings have to be defined in the same way in all apps:

```yaml
MyApp:
  mqtt_prefix: awtrix_XXXX  # The MQTT prefix where Awtrix Light is listening
  icon: "1337"  # Icon to use for the app. Needs to be installed on the device
  sound: "tri"  # Sound to play on notifications (optional), needs to be installed on the device
  enabled_entity: "input_boolean.myswitch"  # Homeassistant switch to enable the app (optional)
```

## Timer

The app will automatically pick up on any defined `timer` entities in Homeassistant and display their progress on the clock when they are running or paused. You can define custom icons for particular timers and ignore others and define a sound file to play on completion.

See the source code if you want to change the colors of the progress bar.

![Teatimer](screenshots/teatimer.png)

Example configuration:

```yaml
TimerDisplay:
  module: ustopwatch
  class: UlanziTimerDisplay
  mqtt_prefix: awtrix_XXXX
  icon: "42893"
  sound: "tri"
  custom_icons:
    tea: "35123"  # Use the entity name without the "timer." prefix
  ignore:
    - front_porch_light # ... also here
```

## Proximity

Will display the proximity of different persons to the home when they are not at a defined location. Makes use of the Homeassistant `device_tracker` and `proximity` integrations to display proximity and direction of travel.

Example configuration:

```yaml
MyProximity:
  module: uproximity
  class: UlanziProximityInfo
  mqtt_prefix: awtrix_XXXX
  icon: "5869"
  tracker: device_tracker.myphone
  proximity_sensor: proximity.me
  person: ict  # Friendly name to display: "ict: 1.2 km <<<"
```

## Weather

A basic weather display. Shows current conditions (with optional second sensor for local measurements) and today's (it it is before 18:00) or tomorrow's forecast with a progress bar for the probability of rain. Has only been tested with the OpenWeathermap integration.

> [!NOTE]  
> You will need to adapt the icon definitions in the source code for the different weather states to your needs and download all defined icons for the best effect. Some icons from the LaMetric library are broken on Awtrix Light and need to be re-saved without compression to look nice.

![Current Weather](screenshots/weather.png)
![Forecast](screenshots/weather2.png)

Example configuration:

```yaml
UlanziWeather:
  module: uweather
  class: UlanziWeather
  mqtt_prefix: awtrix_XXXX
  icon: "0"  # Not used in this app since we use different icons for all conditions
  weather_entity: weather.openweathermap
  current_temp_sensor: sensor.balkon_temperature  # optional
```

## Window Status

Displays open windows.

![Windows](screenshots/windows.png)

Example configuration:

```yaml
UlanziWindowStatus:
  module: uwindow
  class: UlanziWindowAlert
  icon: "47934"
  mqtt_prefix: awtrix_XXXX
  windows:
    - entity: binary_sensor.patio_window_contact  # Sensor entity
      name: Patio  # Short name to display
    - entity: binary_sensor.pool_room_right_contact
      name: Pool R
```

## Humidity Warning

Activates an indicator light when humidity in a defined room reaches a threshold. It will display these rooms once when they reach the threshold and can also display the list again on a keypess.

![Humidity](screenshots/humidity.png)

Example configuration:

```yaml
HumidityNotifier:
  module: uhumidity
  class: UlanziHumidityWarning
  mqtt_prefix: awtrix_XXXX
  icon: "2423"
  sensors:
    - entity: sensor.pool_sensor_humidity
      name: Pool
    - entity: sensor.library_sensor_humidity
      name: Library
  threshold: 60
  indicator: light.awtrix_XXXX_indicator_2  # indicator to use
  indicator_color: [130, 192, 255]  # color of indicator (RGB), optional
  show_buttons:  # list of entities that, when switched to 'on', will re-display the room-list
    - binary_sensor.awtrix_XXX_button_select  # middle button of the clock
    - input_button.ulanzi_show_hum
```