# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json

from neon_utils.skills.neon_skill import NeonSkill
from adapt.intent import IntentBuilder
from os import listdir, path

from mycroft.skills import skill_api_method


class AboutSkill(NeonSkill):
    def __init__(self):
        super(AboutSkill, self).__init__(name="AboutSkill")
        self.skill_info = None
        self._update_skills_data()

    def initialize(self):
        license_intent = IntentBuilder("license_intent").\
            optionally("Neon").optionally("Long").require("Tell").require("License").build()
        self.register_intent(license_intent, self.read_license)

        list_skills_intent = IntentBuilder("list_skills_intent").optionally("Neon").optionally("Tell").\
            require("Skills").build()
        self.register_intent(list_skills_intent, self.list_skills)
        # TODO: Reload skills list when skills are added/removed DM

    def read_license(self, message):
        """
        Reads back the NeonAI license from skill dialog
        :param message: Message associated with request
        """
        if self.neon_in_request(message):
            if message.data.get("Long"):
                self.speak_dialog("license_long")
            else:
                self.speak_dialog("license_short")

    def list_skills(self, message):
        """
        Lists all installed skills by name.
        :param message: Message associated with request
        """
        if self.neon_in_request(message):
            skills_list = [s['title'] for s in self.skill_info if s.get('title')]
            skills_list.sort()
            skills_to_speak = ", ".join(skills_list)
            self.speak_dialog("skills_list", data={"list": skills_to_speak})

    @skill_api_method
    def skill_info_examples(self):
        """
        API Method to build a list of examples as listed in skill metadata.
        """
        examples = [d.get('examples') or list() for d in self.skill_info]
        flat_list = [item for sublist in examples for item in sublist]
        return flat_list

    def _update_skills_data(self):
        """
        Loads skill metadata for all installed skills.
        """
        skills = list()
        skills_dir = path.dirname(path.dirname(__file__))
        for skill in listdir(skills_dir):
            if path.isdir(path.join(skills_dir, skill)) and path.isfile(path.join(skills_dir, skill, "__init__.py")):
                if path.isfile(path.join(skills_dir, skill, "skill.json")):
                    with open(path.join(skills_dir, skill, "skill.json")) as f:
                        skill_data = json.load(f)
                else:
                    skill_name = str(path.basename(skill).split('.')[0]).replace('-', ' ').lower()
                    skill_data = {"title": skill_name}
                skills.append(skill_data)
        self.skill_info = skills

    def stop(self):
        pass


def create_skill():
    return AboutSkill()
