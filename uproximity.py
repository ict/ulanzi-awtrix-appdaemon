from ulanzi import UlanziApp


class UlanziProximityInfo(UlanziApp):

    def initialize(self):
        super().initialize()
        self.last_distance = 0
        self.last_location = None
        try:
            self.tracker = self.args['tracker']
            self.proximity_sensor = self.args['proximity_sensor']
            self.person = self.args['person']
            self.change_threshold = self.args.get('change_threshold', 10)
        except KeyError as err:
            self.error("Failed getting configuration {}".format(err.args[0]))
            return

        self.listen_state(self.proximity_change, self.proximity_sensor)
        self.listen_state(self.proximity_change, self.tracker)

    def proximity_change(self, entity, attribute, old, new, kwargs):
        tracker_state = self.get_state(self.tracker)
        self.log(f"Tracker state: {tracker_state}")
        if tracker_state != 'not_home':
            self.delete_app()
            self.last_distance = 0
            if tracker_state != self.last_location:
                self.send_notification(f"{self.person} @ {tracker_state}")
                self.last_location = tracker_state
            return

        if entity == self.proximity_sensor:
            self.log(f"Proximity change: {old} -> {new}")
            self.log(f"Last distance: {self.last_distance} | Last location: {self.last_location}")
            if old == new or new == self.last_distance:
                return
            if abs(int(new) - int(self.last_distance)) >= self.change_threshold:
                self.last_distance = new
                self.update_app()


    def get_app_text(self):
        state = self.get_state(self.proximity_sensor, attribute='all')
        dir = state['attributes']['dir_of_travel']
        distance = int(state['state'])
        if distance < 1000:
            unit = 'm'
        else:
            distance = round(distance / 1000, 1)
            unit = 'km'
        return f"{self.person}: {distance} {unit} {'<<<' if dir == 'towards' else '>>>'}"
