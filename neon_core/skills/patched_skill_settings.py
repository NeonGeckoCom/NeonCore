# TODO: Deprecate with ovos-backend-client update
try:
    import ovos_workshop.settings
    from ovos_workshop.settings import SkillSettingsManager as _SM
    from ovos_backend_client.api import DeviceApi
    from mock import Mock

    class SkillSettingsManager(_SM):
        def __init__(self, skill):
            self.download_timer = None
            self.skill = skill
            self.api = DeviceApi()
            self.remote_settings = Mock()
            self.register_bus_handlers()

    ovos_workshop.settings.SkillSettingsManager = SkillSettingsManager
except ImportError:
    pass
