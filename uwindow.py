from ulanzi import UlanziApp


class UlanziWindowAlert(UlanziApp):

    def initialize(self):
        super().initialize()
        self.open_windows = set()
        try:
            self.windows = self.args['windows']
        except KeyError as err:
            self.error("Failed getting configuration {}".format(err.args[0]))
            return

        for window in self.windows:
            window_entity = window['entity']
            window_name = window['name']
            self.listen_state(self.window_action, window_entity, window_name=window_name)

        self.log(f"Initialized {len(self.windows)} windows")

    def window_action(self, entity, attribute, old, new, kwargs):
        window_name = kwargs['window_name']
        if old != new and new == 'on':
            self.open_windows.add(window_name)
        elif old != new and new == 'off':
            try:
                self.open_windows.remove(window_name)
            except KeyError:
                pass

        if len(self.open_windows) > 0:
            self.update_app()
        else:
            self.delete_app()

    def get_app_text(self):
        return ", ".join(self.open_windows)