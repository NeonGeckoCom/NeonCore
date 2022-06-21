from mycroft.skills import MycroftSkill


class OVOSTestSkill(MycroftSkill):
    def __init__(self):
        super(OVOSTestSkill, self).__init__(name="OVOSTestSkill")
        self.is_a_skill = False


def create_skill():
    return OVOSTestSkill()
