# TODO: Remove below patches with ovos-core 0.0.8
import mycroft.skills.skill_loader
from mycroft.skills.skill_loader import PluginSkillLoader as _Plugin


class PluginSkillLoader(_Plugin):
    def __int__(self, *args, **kwargs):
        _Plugin.__init__(self, *args, **kwargs)

    def load(self, skill_class=None):
        skill_class = skill_class or self._skill_class
        _Plugin.load(self, skill_class)


mycroft.skills.skill_loader.PluginSkillLoader = PluginSkillLoader
