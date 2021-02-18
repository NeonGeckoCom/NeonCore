from mycroft.util.log import LOG


class OldNeonCompatibilitySkill:
    """
    This skill exposes dummy methods for skill compatibility
    It is meant only to address missing methods and will be deprecated in
    the future, this is essentially a placeholder to avoid syntax errors
    """
    def preference_brands(self, *args, **kwargs) -> dict:
        """
        Returns a brands dictionary for the user
        Equivalent to self.user_info_available["speech"] for non-server use
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")
        return {'ignored_brands': {},
                'favorite_brands': {},
                'specially_requested': {}}

    def preference_user(self, *args, **kwargse) -> dict:
        """
        Returns the user dictionary with name, email
        Equivalent to self.user_info_available["user"] for non-server use
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")
        return {'first_name': '',
                'middle_name': '',
                'last_name': '',
                'preferred_name': '',
                'full_name': '',
                'dob': 'YYYY/MM/DD',
                'age': '',
                'email': '',
                'username': '',
                'password': '',
                'picture': '',
                'about': '',
                'phone': '',
                'email_verified': False,
                'phone_verified': False
                }

    def preference_location(self, *args, **kwargs) -> dict:
        """
        Get the JSON data structure holding location information.
        Equivalent to self.user_info_available["location"] for non-server use
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")
        return {'lat': 47.4799078,
                'lng': -122.2034496,
                'city': 'Renton',
                'state': 'Washington',
                'country': 'USA',
                'tz': 'America/Los_Angeles',
                'utc': -8.0
                }

    def preference_unit(self, *args, **kwargs) -> dict:
        """
        Returns the units dictionary that contains time, date, measure formatting preferences
        Equivalent to self.user_info_available["units"] for non-server use
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")
        return {'time': 12,
                'date': 'MDY',
                'measure': 'imperial'
                }

    def preference_speech(self, *args, **kwargs) -> dict:
        """
        Returns the speech dictionary that contains language and spoken response preferences
        Equivalent to self.user_info_available["speech"] for non-server use
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")
        return {'stt_language': 'en',
                'stt_region': 'US',
                'alt_languages': ['en'],
                'tts_language': "en-us",
                'tts_gender': 'female',
                'neon_voice': 'Joanna',
                'secondary_tts_language': '',
                'secondary_tts_gender': '',
                'secondary_neon_voice': '',
                'speed_multiplier': 1.0,
                'synonyms': {}
                }

    def preference_skill(self, *args, **kwargs) -> dict:
        """
        Returns the skill settings configuration
        Equivalent to self.settings for non-server
        :param message: Message associated with request
        :return: dict of skill preferences
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")
        return {}

    def update_profile(self, *args, **kwargs):
        """
        Updates a user profile with the passed new_preferences
        :param new_preferences: dict of updated preference values. Should follow {section: {key: val}} format
        :param message: Message associated with request
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")

    def update_skill_settings(self, *args, **kwargs):
        """
        Updates skill settings with the passed new_preferences
        :param new_preferences: dict of updated preference values. {key: val}
        :param message: Message associated with request
        :param skill_global: Boolean to indicate these are global/non-user-specific variables
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")

    def get_utterance_user(self, *args, **kwargs):
        """
        Get the user associated with the message
        :param message: message object to evaluate
        :return: user associated with request; 'local' if not specified
        """
        func_name = self.preference_brands.__name__
        LOG.warning(f"MycroftSkill.{func_name} has been deprecated!")
        return "local"
