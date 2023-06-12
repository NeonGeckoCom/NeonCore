# TODO: Remove below patches with ovos-core 0.0.8
import mycroft.skills.skill_loader
from mycroft.skills.skill_loader import PluginSkillLoader as _Plugin
from ovos_bus_client.message import Message
from ovos_utils.log import LOG

try:
    from ovos_workshop.skill_launcher import get_skill_class, \
        get_create_skill_function
except ImportError:
    get_skill_class, get_create_skill_function = None, None


class PluginSkillLoader(_Plugin):
    def __int__(self, *args, **kwargs):
        _Plugin.__init__(self, *args, **kwargs)

    def load(self, skill_class=None):
        skill_class = skill_class or self._skill_class
        _Plugin.load(self, skill_class)

    def _create_skill_instance(self, skill_module=None):
        if get_skill_class is None:
            return super()._create_skill_instance(skill_module)
        try:
            # in skill classes __new__ should fully create the skill object
            skill_class = get_skill_class(skill_module)
            self.instance = skill_class(bus=self.bus, skill_id=self.skill_id)
            return self.instance is not None
        except Exception as e:
            LOG.warning(f"Skill load raised exception: {e}")

        try:
            # attempt to use old style create_skill function entrypoint
            skill_creator = get_create_skill_function(skill_module) or \
                self.skill_class
        except Exception as e:
            LOG.exception(f"Failed to load skill creator: {e}")
            self.instance = None
            return False

        # if the signature supports skill_id and bus pass them
        # to fully initialize the skill in 1 go
        try:
            # skills that do will have bus and skill_id available
            # as soon as they call super()
            self.instance = skill_creator(bus=self.bus,
                                          skill_id=self.skill_id)
        except Exception as e:
            # most old skills do not expose bus/skill_id kwargs
            LOG.warning(f"Legacy skill: {e}")
            self.instance = skill_creator()

        try:
            # finish initialization of skill if we didn't manage to inject
            # skill_id and bus kwargs.
            # these skills only have skill_id and bus available in initialize,
            # not in __init__
            if not self.instance._is_fully_initialized:
                self.instance._startup(self.bus, self.skill_id)
        except Exception as e:
            LOG.exception(f'Skill __init__ failed with {e}')
            self.instance = None

        return self.instance is not None


mycroft.skills.skill_loader.PluginSkillLoader = PluginSkillLoader
mycroft.skills.skill_loader.Message = Message
