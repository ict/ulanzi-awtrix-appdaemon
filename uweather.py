import json

from ulanzi import UlanziApp

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
            self.weather_entity_name = self.args['weather_entity']
            self.weather_entity = self.get_entity(self.weather_entity_name)
            self.current_temp_sensor = self.args.get('current_temp_sensor')
        except KeyError as err:
            self.error('Failed getting configuration {}'.format(err.args[0]))
            return

        self.update_app()
        self.run_every(self.update_app, 'now', 300)
        if self.current_temp_sensor:
            self.listen_state(self.update_app, self.current_temp_sensor)

    def real_update_app(self, forecast_obj):
        # Get current state and temperature
        current = self.weather_entity.get_state(attribute='all')
        current_icon = ICON_MAP.get(current['state'], ICON_MAP['exceptional'])
        if self.current_temp_sensor and (t := self.get_state(self.current_temp_sensor)) != 'unknown':
            current_temp = round(float(t), 1)
        else:
            current_temp = round(float(current['attributes']['temperature']), 1)

        if self.now_is_between('00:00:00', '18:00:00'):
            forecast = forecast_obj['forecast'][0]
        else:
            forecast = forecast_obj['forecast'][1]
        temp_tomorrow_low = forecast['templow']
        temp_tomorrow_hight = forecast['temperature']
        temp_tomorrow = f'{int(round(temp_tomorrow_low))} - {int(round(temp_tomorrow_hight))}'
        if temp_tomorrow_hight < 0:
            temp_tomorrow = f'{int(round(temp_tomorrow_low))} | {int(round(temp_tomorrow_hight))}'
        if len(temp_tomorrow) > 7:
            temp_tomorrow = temp_tomorrow.replace(' ', '')
        icon_tomorrow = ICON_MAP.get(forecast['condition'], ICON_MAP['exceptional'])
        preci_tomorrow = forecast['precipitation_probability']

        payload = [
            {
                'icon': current_icon,
                'text': f'{current_temp}°',
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
        if not self.enabled:
            return

        forecast = self.call_service(
            'weather/get_forecasts',
            target={'entity_id': self.weather_entity_name},
            service_data={'type': 'daily'},
        )

        weather_data = None
        try:
            weather_data = forecast['result']['response'][self.weather_entity_name]
        except KeyError:
            import pprint

            self.log('Got unexpected service callback with:' + pprint.pformat(forecast['result']))
            return
        self.real_update_app(weather_data)

    def get_app_text(self):
        raise NotImplementedError
