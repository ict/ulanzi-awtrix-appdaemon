import asyncio
import random
import json
from ulanzi import UlanziApp

"""
CAUTION: Due to Appdaemon's limitations, calling the weather.get_forecasts service
        needs an indirection to get the result of the service call.
        See https://github.com/AppDaemon/appdaemon/issues/1837

        This means you need to add a script to homeassistant with the following content:
```
alias: get_forecast_now
mode: single
icon: mdi:room-service-outline
fields:
  call_id:
    name: Call id
    default: 1
    description: An id to uniquely identify the call
    required: true
    selector:
      text: null
  entity:
    selector:
      entity: {}
    name: entity
sequence:
  - target:
      entity_id: "{{ entity }}"
    data:
      type: daily
    response_variable: response
    action: weather.get_forecasts
  - event: call_service_with_response.finished
    event_data:
      call_id: "{{ call_id }}"
      response: "{{ response }}"
```
"""

ICON_MAP = {
    'rainy': '72',
    'clear-night': '2285',
    # 'cloudy': '2283',
    'cloudy': '53384_',
    'fog': '12196',
    'hail': '2441',
    'lightning': '10341',
    'lightning-rainy': '49299',
    'partlycloudy': 'partlycloudy',
    'pouring': '72',
    'snowy': '2289',
    'snowy-rainy': '49301',
    'sunny': '11201',
    'windy': '55032',
    'windy-variant': '55032',
    'exceptional': '45123',
}


class UlanziWeather(UlanziApp):

    def initialize(self):
        super().initialize()
        try:
            self.weather_entity = self.args['weather_entity']
            self.current_temp_sensor = self.args.get('current_temp_sensor')
        except KeyError as err:
            self.error("Failed getting configuration {}".format(err.args[0]))
            return
        
        self.run_every(self.update_app, 'now', 60)
        if self.current_temp_sensor:
            self.listen_state(self.update_app_custom, self.current_temp_sensor)
    
    def schedule_call_service(self):
        # call with result, using the script wrapper
        call_id = random.randrange(2**32)

        self.listen_event(
            self.real_update_app,
            "call_service_with_response.finished",
            call_id=call_id,
            oneshot=True,
        )

        self.call_service(
            "script/get_forecast_now",
            entity=self.weather_entity,
            call_id=call_id,
        )

    def update_app_custom(self, *args, **kwargs):
        if not self.enabled:
            return

        # Get forecast for tomorrow, this must be done as a callback
        forecast = self.schedule_call_service()

    def real_update_app(self, event_name, data, kwargs):
        # Get current state and temperature
        current = self.get_state(self.weather_entity, attribute='all')
        current_icon = ICON_MAP.get(current['state'], ICON_MAP['exceptional'])
        if self.current_temp_sensor and (t := self.get_state(self.current_temp_sensor)) != 'unknown':
            current_temp = round(float(t), 1)
        else:
            current_temp = round(float(current['attributes']['temperature']), 1)

        # Get forecast for tomorrow
        forecast_obj = data['response']

        if self.now_is_between('00:00:00', '18:00:00'):
            forecast = forecast_obj[self.weather_entity]['forecast'][0]
        else:
            forecast = forecast_obj[self.weather_entity]['forecast'][1]
        temp_tomorrow_low = forecast['templow']
        temp_tomorrow_hight = forecast['temperature']
        temp_tomorrow = f"{int(round(temp_tomorrow_low))} - {int(round(temp_tomorrow_hight))}"
        if temp_tomorrow_hight < 0:
            temp_tomorrow = f"{int(round(temp_tomorrow_low))} | {int(round(temp_tomorrow_hight))}"
        if len(temp_tomorrow) > 7:
            temp_tomorrow = temp_tomorrow.replace(' ', '')
        icon_tomorrow = ICON_MAP.get(forecast['condition'], ICON_MAP['exceptional'])
        preci_tomorrow = forecast['precipitation_probability']

        payload = [
            {
                'icon': current_icon,
                'text': f"{current_temp}°",
            },
            {
                'icon': icon_tomorrow,
                'text': temp_tomorrow,
                'progress': int(preci_tomorrow),
                'progressC': '#2562c4',
                'progressBC': '#373a40',
            },
        ]
        self.call_service('mqtt/publish', topic=self.mqtt_app_topic, payload=json.dumps(payload))
        # self.log(f"Updated display: {current_temp} | {temp_tomorrow}")

    def update_app(self, *args, **kwargs):
        self.update_app_custom()

    def get_app_text(self):
        raise NotImplementedError
