#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'mycroft-homescreen.mycroftai=ovos_skill_homescreen:OVOSHomescreenSkill'
# in this case the skill_id is defined to purposefully replace the mycroft version of the skill,
# or rather to be replaced by it in case it is present. all skill directories take precedence over plugin skills


setup(
    # this is the package name that goes on pip
    name='ovos-skill-homescreen',
    version='0.0.1',
    description='OVOS homescreen skill plugin',
    url='https://github.com/OpenVoiceOS/skill-ovos-homescreen',
    author='Aix',
    author_email='aix.m@outlook.com',
    license='Apache-2.0',
    package_dir={"ovos_skill_homescreen": ""},
    package_data={'ovos_skill_homescreen': ["vocab/*", "ui/*"]},
    packages=['ovos_skill_homescreen'],
    include_package_data=True,
    install_requires=["ovos-plugin-manager>=0.0.2", "astral==1.4", "arrow==0.12.0"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
