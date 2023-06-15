try:
    import mycroft.deprecated.skills.settings
    from mycroft.deprecated.skills.settings import SettingsMetaUploader as _SM

    class SettingsMetaUploader(_SM):
        def __int__(self, skill_directory: str, skill_name: str = "",
                    skill_id: str = None):
            if not skill_id:
                skill_id = skill_name
            _SM.__init__(self, skill_directory=skill_directory,
                         skill_id=skill_id)

    mycroft.deprecated.skills.settings.SettingsMetaUploader = SettingsMetaUploader
except ImportError:
    pass
