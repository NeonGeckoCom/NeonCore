from mycroft.skills.intent_service_interface import IntentQueryApi
from mycroft.configuration import Configuration
from mycroft.text_parsing.modules import TextParser


class SkillAuth(TextParser):
    def __init__(self, name="admin_skills", priority=6):
        super().__init__(name, priority)
        self.intents = None
        skills_config = Configuration.get().get("skills", {})
        self.admin_skills = skills_config.get("admin_skills", [])

    def bind(self, bus):
        super().bind(bus)
        self.intents = IntentQueryApi(self.bus)

    def parse(self, utterances, user, lang="en-us"):
        data = {"blocked_utterances": []}
        if user is None or not user.is_admin:
            for idx, utterance in enumerate(utterances):
                skill = self.intents.get_skill(utterance, lang)
                if skill in self.admin_skills:
                    utterances[idx] = "say not authorized to perform this " \
                                      "action"
                    data["blocked_utterances"].append(utterance)

        # return utterances + data
        return utterances, data


def create_parser():
    return SkillAuth()



