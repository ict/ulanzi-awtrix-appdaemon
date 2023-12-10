from abc import ABC, abstractmethod
import json
import appdaemon.plugins.hass.hassapi as hass

class UlanziApp(hass.Hass):
    """
    Base class for all Ulanzi apps, supports apps as well as notifications
    and stores basic configuration
    """

    def initialize(self):
        try:
            self.prefix = self.args['mqtt_prefix']
            self.icon = self.args['icon']
            self.sound = self.args.get('sound', None)
            self.enabled_entity = self.args.get('enabled_entity', None)
        except KeyError as err:
            self.error("Failed getting configuration {}".format(err.args[0]))
            return

        if self.enabled_entity:
            self.listen_state(self.delete_app, self.enabled_entity, new='off')
            self.listen_state(self.update_app, self.enabled_entity, new='on')

    @property
    def app_name(self):
        return self.name

    @property
    def mqtt_app_topic(self):
        return f'{self.prefix}/custom/{self.app_name}'

    @property
    def enabled(self):
        if self.enabled_entity:
            return self.get_state(self.enabled_entity) == 'on'
        return True

    def get_additional_properties(self):
        """ Override this method to add additional properties to the MQTT payload """
        return {}

    @abstractmethod
    def get_app_text(self):
        """ Override this method to return the text to be displayed on the Ulanzi """
        pass

    def update_app(self, *args, **kwargs):
        """ Call this method from your subclass to update the app on the Ulanzi """
        if not self.enabled:
            return
        text = self.get_app_text()
        additional_properties = self.get_additional_properties()
        mqtt_payload = {
            'icon': self.icon,
            'text': text,
            'lifetime': 60*60  # 1 hour failsafe
        }
        if additional_properties:
            mqtt_payload.update(additional_properties)

        # Call homeassistant service to update the app over MQTT
        self.log(f"Sending app update for {self.app_name}: {text}")
        self.call_service('mqtt/publish', topic=self.mqtt_app_topic, payload=json.dumps(mqtt_payload))

    def delete_app(self, *args, **kwargs):
        self.call_service('mqtt/publish', topic=self.mqtt_app_topic, payload='{}')

    def send_notification(self, message, icon=None, sound=None, **kwargs):
        self.log(f"Sending notification: {message}")
        payload = {
            'text': message,
            'icon': icon or self.icon,
            'repeat': 2,
        }
        if self.sound:
            payload['sound'] = self.sound
        if sound:
            payload['sound'] = sound
        if kwargs:
            payload.update(kwargs)
        self.call_service('mqtt/publish', topic=f'{self.prefix}/notify', payload=json.dumps(payload))


