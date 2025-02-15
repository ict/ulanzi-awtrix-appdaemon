import json
from dataclasses import dataclass
from datetime import datetime, timezone
import time
from ulanzi import UlanziApp

BAR_COLOR_PAUSED = '#deb764'
BAR_COLOR_RUNNING = '#aadb72'
BAR_COLOR_BG = '#373a40'


class UlanziTimerDisplay(UlanziApp):
    """
    App that listens to HASS timer events and dynamically displays them
    """

    TIMER_STARTED = 'timer.started'
    TIMER_FINISHED = 'timer.finished'
    TIMER_CANCELLED = 'timer.cancelled'
    TIMER_PAUSED = 'timer.paused'
    TIMER_RESTARTED = 'timer.restarted'

    @dataclass
    class Timer:
        status: str
        remaining: int
        total: int
        icon: str

        def get_output(self):
            if self.remaining >= 3600:
                text = time.strftime('%-H:%M:%S', time.gmtime(self.remaining))
            else:
                text = time.strftime('%-M:%S', time.gmtime(max(0, self.remaining)))
            result = {
                'icon': self.icon,
                'text': text,
                'progressBC': BAR_COLOR_BG,
                'progressC': BAR_COLOR_RUNNING if self.status == 'running' else BAR_COLOR_PAUSED,
                'progress': int(100 - (self.remaining / self.total * 100)),
                'lifetime': self.remaining + 30
            }
            if self.remaining < 30:
                result['duration'] = 30
            return result

    def initialize(self):
        super().initialize()
        self.timers = {}
        self.tick_timer_handle = None
        try:
            self.custom_icons = self.args.get('custom_icons', {})
            self.ignore_timers = self.args.get('ignore', [])
        except KeyError as err:
            self.error("Failed getting configuration {}".format(err.args[0]))
            return
        
        timer_events = [
            UlanziTimerDisplay.TIMER_STARTED,
            UlanziTimerDisplay.TIMER_FINISHED,
            UlanziTimerDisplay.TIMER_CANCELLED,
            UlanziTimerDisplay.TIMER_PAUSED,
            UlanziTimerDisplay.TIMER_RESTARTED,
        ]
        self.listen_event(self.trigger, timer_events)

    def _get_seconds_until(self, timestamp):
        """Get the amount of seconds until the given timestamp"""
        now = datetime.now(timezone.utc)
        then = datetime.fromisoformat(timestamp)
        return int((then - now).total_seconds())

    def trigger(self, event_name, data, kwargs):
        self.log(f"Received event {event_name}: {data}")
        timer_id = data['entity_id']
        timer_name = timer_id.split('.')[-1]

        if timer_id in self.ignore_timers or timer_name in self.ignore_timers:
            return

        timer = self.get_state(timer_id, attribute='all')
        icon = self.custom_icons.get(timer_name, self.icon)

        if event_name in (UlanziTimerDisplay.TIMER_STARTED):
            self.timers[timer_id] = UlanziTimerDisplay.Timer(
                status='running',
                remaining=self._get_seconds_until(timer['attributes']['finishes_at']),
                total=self._get_seconds_until(timer['attributes']['finishes_at']),
                icon=icon,
            )
        else:
            obj = self.timers.get(timer_id)
            if obj is None:
                self.log(f"Received event {event_name} for unknown timer {timer_id}")
                return
            if event_name == UlanziTimerDisplay.TIMER_RESTARTED:
                obj.remaining = self._get_seconds_until(timer['attributes']['finishes_at']) + 1
                obj.status = 'running'
            elif event_name == UlanziTimerDisplay.TIMER_FINISHED:
                del self.timers[timer_id]
                timer_name = timer['attributes']['friendly_name']
                self.send_notification(f"{timer_name} ist fertig!", icon=icon)
            elif event_name == UlanziTimerDisplay.TIMER_CANCELLED:
                del self.timers[timer_id]
            elif event_name == UlanziTimerDisplay.TIMER_PAUSED:
                obj.status = 'paused'

        if not self.timers:
            self.delete_app()
            self.cancel_timer(self.tick_timer_handle)
            self.tick_timer_handle = None

        elif self.tick_timer_handle is None:
            self.tick_timer_handle = self.run_every(self.tick, 'now', 1)

    def tick(self, *args, **kwargs):
        app_pages = []
        for timer in self.timers.values():
            if timer.status == 'running':
                timer.remaining -= 1
            app_pages.append(timer.get_output())
        
        self.call_service('mqtt/publish', topic=self.mqtt_app_topic, payload=json.dumps(app_pages))
