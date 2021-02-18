from mycroft.skills.skill_store import SkillsStore

# this can be run as an install step
s = SkillsStore()
for skill, was_updated in s.install_default_skills():
    if was_updated:
        print(skill, "was installed/updated")
    else:
        print(skill, "didn't change")
