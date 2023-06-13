# TODO: Remove below patches with ovos-core 0.0.8
import mycroft.skills.skill_loader

from ovos_bus_client.message import Message
from ovos_utils.log import LOG

try:
    from ovos_workshop.skill_launcher import PluginSkillLoader
    from ovos_workshop.skill_launcher import get_skill_class, \
        get_create_skill_function
except ImportError:
    LOG.warning(f"Patching PluginSkillLoader")
    from mycroft.skills.skill_loader import PluginSkillLoader as _Plugin
    get_skill_class, get_create_skill_function = None, None


    class PluginSkillLoader(_Plugin):
        def __int__(self, *args, **kwargs):
            _Plugin.__init__(self, *args, **kwargs)

        def load(self, skill_class=None):
            skill_class = skill_class or self._skill_class
            _Plugin.load(self, skill_class)


mycroft.skills.skill_loader.PluginSkillLoader = PluginSkillLoader
mycroft.skills.skill_loader.Message = Message
