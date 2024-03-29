from ulanzi import UlanziApp


class UlanziHumidityWarning(UlanziApp):

    def initialize(self):
        super().initialize()
        self.sensors_above = set()
        try:
            self.sensors = self.args['sensors']
            self.threshold = self.args['threshold']
            self.indicator = self.args['indicator']
            self.indicator_color = self.args.get('indicator_color', [130, 192, 255])
            self.show_buttons = self.args.get('show_buttons', [])
        except KeyError as err:
            self.error("Failed getting configuration {}".format(err.args[0]))
            return

        for sensor in self.sensors:
            sensor_entity = sensor['entity']
            sensor_name = sensor['name']
            current_state = self.get_state(sensor_entity)
            self.log(f"Current state of {sensor_name}: {current_state}")
            try:
                if float(current_state) > self.threshold:
                    self.sensors_above.add(sensor_name)
                    self.log(f"Adding {sensor_name} to sensors_above")
            except ValueError:
                self.log(f"{sensor}: Could not parse {current_state} as float")

            self.listen_state(self.sensor_change, sensor_entity, sensor_name=sensor_name)

        if not isinstance(self.show_buttons, list):
            self.show_buttons = [self.show_buttons]
        for button in self.show_buttons:
            self.listen_state(self.show_humidity, button)
        self.update_state(False)

    def sensor_change(self, entity, attribute, old, new, kwargs):
        sensor_name = kwargs['sensor_name']
        new_sensor = False

        try:
            humidity = float(new)
        except ValueError:
            self.log(f"{entity}: Could not parse {new} as float")
            return
        if humidity > self.threshold:
            # self.log(f"Over thresh")
            if sensor_name not in self.sensors_above:
                new_sensor = True
                self.sensors_above.add(sensor_name)
        elif sensor_name in self.sensors_above:
            # self.log(f"No longer over thresh")
            self.sensors_above.remove(sensor_name)

        self.update_state(new_sensor)

    def update_state(self, new_sensor):
        if not self.sensors_above:
            self.turn_off(self.indicator)
        else:
            self.turn_on(self.indicator, rgb_color=self.indicator_color)
        if new_sensor:
            self.show_humidity('fake', 'params', 'old', 'off', 'kwargs')

    def show_humidity(self, entity, attribute, old, new, kwargs):
        self.log(f"old: {old}, new: {new}")
        if old == new or new == 'on' or new == 'unavailable':
            return  # Generally trigger on button release, but not if new value is not meaningful
        entries = []
        if self.sensors_above:
            # Send a new notification
            for sensor in self.sensors:
                if sensor['name'] in self.sensors_above:
                    entries.append(f"{sensor['name']}: {self.get_state(sensor['entity'])}%")
            self.send_notification(" | ".join(entries))
        else:
            # Show all sensors
            for sensor in self.sensors:
                entries.append(f"{sensor['name']}: {self.get_state(sensor['entity'])}%")
            self.send_notification(" | ".join(entries))

    def get_app_text(self):
        raise NotImplementedError  # We are not using base class implementation
