from mycroft.util.log import LOG
from mycroft.util import connected
from mycroft.skills.skill_manager import SkillManager
from neon_core.skills.skill_store import SkillsStore
from neon_utils.configuration_utils import get_neon_skills_config

SKILL_MAIN_MODULE = '__init__.py'


class NeonSkillManager(SkillManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skill_config = kwargs.get("config") or get_neon_skills_config()
        self.skill_downloader = SkillsStore(skills_dir=self.skill_config["directory"], config=self.skill_config,
                                            bus=self.bus)
        self.skill_downloader.skills_dir = self.skill_config["directory"]

    def download_or_update_defaults(self):
        # on launch only install if missing, updates handled separately
        # if osm is disabled in .conf this does nothing
        if self.skill_config["auto_update"]:
            try:
                self.skill_downloader.install_default_skills()
            except Exception as e:
                if connected():
                    # if there is internet log the error
                    LOG.exception(e)
                    LOG.error("default skills installation failed")
                else:
                    # if no internet just skip this update
                    LOG.error("no internet, skipped default skills installation")
            
    def run(self):
        """Load skills and update periodically from disk and internet."""
        self.download_or_update_defaults()
        super().run()

    def _emit_converse_error(self, message, skill_id, error_msg):
        super()._emit_converse_error(message, skill_id, error_msg)
        # Also emit the old error message to keep compatibility and for any
        # listener on the bus
        reply = message.reply('skill.converse.error',
                              data=dict(skill_id=skill_id, error=error_msg))
        self.bus.emit(reply)
