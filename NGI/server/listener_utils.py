# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

from NGI.utilities.chat_user_util import ChatUser
from mycroft.messagebus import MessageBusClient
from mycroft.util import LOG, create_daemon


class ServerListener:
    def __init__(self):
        # self.emitter = emitter
        # self.shouts_folder = self.emitter.configuration_available["dirVars"]["docsDir"] + "/"
        self.chat_user_dict = {}
        # self.audio_normalizer = AudioNormalizer()
        # self.minimum_level = -25.0
        # self.minimum_length = 4.0

        bus = MessageBusClient()  # Mycroft messagebus, see mycroft.messagebus
        # Configuration.init(bus)
        bus.on('neon.remove_cache_entry', self.remove_cached_profile)
        create_daemon(bus.run_forever)

    # moved to neon_utils
    # @staticmethod
    # def get_most_recent(path: str) -> Optional[str]:
    #     """
    #     Gets the most recently created file in the specified path
    #     :param path: File path to check
    #     :return: Path to newest file in specified path
    #     """
    #     list_of_files = glob.glob(path)  # * means all if need specific format then *.csv
    #     if list_of_files:
    #         latest_file = max(list_of_files, key=os.path.getctime)
    #         return latest_file
    #     else:
    #         return None

    # def handle_audio_input(self) -> (str, AudioData):
    #     """
    #     Handles server audio input (for Neon STT). Called when "FileInputToSTT" signal is set
    #     :return: flac_filename, audio data (None if audio too quiet)
    #     """
    #     LOG.debug(f">>>>> Incoming! (FileInputToSTT)")
    #     audio = None
    #     flac_filename = get_most_recent(
    #         '/var/www/html/klatchat/app/files/chat_audio/sid-*.flac')
    #     if not flac_filename:
    #         check_for_signal('FileInputToSTT')
    #         LOG.info(''' AudioConsumer returning, no input flac files, device = server''')
    #         return
    #     try:
    #         LOG.info(''' flac_filename to read = ''' + str(flac_filename))
    #         song = AudioSegment.from_file(flac_filename)
    #
    #         LOG.info(song.dBFS)
    #         LOG.info(song.duration_seconds)
    #
    #         # LOG.debug("DM: This One")
    #         nano = get_nano_param_from_filename(flac_filename)
    #
    #         # TODO also check for the physical file length?
    #         if song.dBFS > self.minimum_level or song.duration_seconds > self.minimum_length or nano == 'mobile':
    #             LOG.info('audio loud or long  enough to use.')
    #             audio = AudioData(open(flac_filename, "rb").read(), 16000, 1)
    #             # os.system('cp ' + str(self.flac_filename) + ' /tmp/stt-text.flac')
    #         else:
    #             LOG.info('audio too quiet or too short.')
    #             audio = None
    #             self.emitter.emit("recognizer_loop.server_response",
    #                               {"event": "audio too quiet from mycroft",
    #                                "data": [flac_filename]})
    #             return
    #
    #         os.system('cp ' + str(flac_filename) + ' /tmp/stt-text.flac')
    #
    #     except Exception as x:
    #         LOG.error(f"audio file open error == {x}")
    #     finally:
    #         if audio is not None:
    #             basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    #             LOG.info('basedir = ' + basedir)
    #             try:
    #                 LOG.info(f" username = {pwd.getpwuid(os.getuid()).pw_name}")
    #                 ensure_directory_exists(self.shouts_folder, "shouts_audio")
    #                 # Transcribe().check_dir("shouts_audio/")
    #                 mv_to_directory = " " + self.shouts_folder + "shouts_audio/"
    #                 command = 'mv ' + str(flac_filename) \
    #                           + mv_to_directory \
    #                           + os.path.basename(str(flac_filename))
    #                 p = os.system(command)
    #                 LOG.info('''move command == ''' + str(command))
    #                 LOG.info('''move command return == ''' + str(p))
    #             except Exception as x:
    #                 LOG.error(f"move command error == {str(x)}")
    #         else:
    #             try:
    #                 p = os.system('rm ' + str(flac_filename))
    #                 LOG.info(f"remove command return == {p}")
    #             except Exception as x:
    #                 LOG.error('error removing...')
    #                 LOG.error(x)
    #         return flac_filename, audio
    #
    # def handle_text_input(self):
    #     """
    #     Handles server text input. Called when "TextFileInput" signal is set
    #     :return: text_filename, audio data
    #     """
    #     audio = None
    #     audiofile = None
    #     text_filename = get_most_recent(
    #         '/var/www/html/klatchat/app/files/shout_text/sid-*')  # .92
    #     utterance = ''
    #     if not text_filename:
    #         check_for_signal('TextFileInput')
    #         LOG.info(''' AudioConsumer returning, no input text files, device = server''')
    #         return None, None
    #     try:
    #         LOG.info(''' text_filename to read = ''' + str(text_filename))
    #         try:
    #             with open(text_filename, mode='rb') as fd:
    #                 tmp_utterance = fd.read()
    #                 fd.close()
    #             # tmpUtterances = fd.readline()
    #             # Decoding the Base64 bytes
    #             d = base64.b64decode(tmp_utterance)
    #             # Decoding the bytes to string
    #             s2 = d.decode("UTF-8")
    #             utterance = html.unescape(s2)
    #             utterance = normalize(utterance, remove_articles=False)
    #             LOG.debug(f">>>>> Incoming! {utterance}")
    #         except Exception as f:
    #             LOG.error(f"text file open error == {str(f)}")
    #             LOG.error(text_filename)
    #             LOG.error(tmp_utterance)
    #
    #         try:
    #             sid = get_shout_id_from_filename(text_filename)
    #             audio_file = get_most_recent(
    #                 f'/var/www/html/klatchat/app/files/chat_audio/sid-{sid}*.flac')
    #         except Exception as x:
    #             LOG.error(x)
    #             audio_file = None
    #
    #         LOG.info(str(utterance))
    #         nano = get_nano_param_from_filename(text_filename)
    #         nick = get_chat_nickname_from_filename(text_filename)
    #
    #         # Handle all of the transcription service things if we have audio
    #         if audio_file:
    #
    #             def get_ip_address():
    #                 s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #                 s.connect(("8.8.8.8", 80))
    #                 return s.getsockname()[0]
    #
    #             sudo_password = ''
    #             for server, password in list(NGIConfig("ngi_auth_vars").content['servers'].items()):
    #                 if server in get_ip_address():
    #                     sudo_password = password
    #
    #             LOG.info(f"GD: Audio file found with text shout")
    #             LOG.info(f"GD: audio_file = {audio_file}  of size: {os.path.getsize(audio_file)}")
    #             my_audio = AudioSegment.from_file(audio_file, sample_width=2, frame_rate=16000,
    #                                               channels=1)
    #             LOG.debug(f"GD: Audio Segment of length {my_audio.duration_seconds} created")
    #             my_audio.export(audio_file, format="wav")
    #             song = AudioSegment.from_wav(audio_file)
    #             audio_data = self.audio_normalizer.trim_silence_and_normalize(song)
    #
    #             # LOG.info(song.dBFS)
    #             # LOG.info(song.duration_seconds)
    #             # start_trim = self.detect_leading_silence(song, song.dBFS + 10)
    #             # LOG.info(start_trim)
    #             # end_trim = self.detect_leading_silence(song.reverse(), song.dBFS)
    #             # LOG.info(end_trim)
    #             #
    #             # duration = len(song)
    #             # LOG.debug(f"GD: start={start_trim} end={end_trim} duration={duration}")
    #             # if start_trim != duration:
    #             #     trimmed_sound = song[start_trim:duration - end_trim]
    #             # else:
    #             #     trimmed_sound = song
    #             # LOG.info(trimmed_sound.duration_seconds)
    #             # LOG.info("here")
    #             # if trimmed_sound.dBFS != -18.0:
    #             #     change_needed = -18.0 - trimmed_sound.dBFS
    #             #     trimmed_sound = trimmed_sound.apply_gain(change_needed)
    #             AudioSegment(
    #                 data=audio_data.frame_data,
    #                 sample_width=audio_data.sample_width,
    #                 frame_rate=audio_data.sample_rate,
    #                 channels=1
    #             ).export(audio_file, format="wav",
    #                      tags={'artist': get_chat_nickname_from_filename(audio_file),
    #                            'album': str(' '),
    #                            'comments': str(' ')})
    #
    #             LOG.info(f"GD: Exported {audio_file} of size: {os.path.getsize(audio_file)}")
    #             audio = audio_data
    #
    #             LOG.info(f"GD: audio.frame_data = {len(audio.frame_data)}")
    #             # os.system('cp ' + str(audio_file) + ' /tmp/stt-text.flac')
    #             mv_to_directory = " " + self.shouts_folder + "shouts_audio/"
    #             # os.system(f"mv {new_audio_file} {mv_to_directory}{os.path.basename(new_audio_file)}")
    #             LOG.info(f"GD: mv {audio_file} {mv_to_directory}{os.path.basename(audio_file)}")
    #             os.system(f"mv {audio_file} {mv_to_directory}{os.path.basename(audio_file)}")
    #
    #             # truncate off .flac
    #             command = (f"cp {mv_to_directory}{os.path.basename(audio_file)} "
    #                        f"{audio_file.split('.')[0]}")
    #
    #             LOG.debug('trim silence, command = ' + command)
    #             p = os.system('echo %s|sudo -S %s' % (sudo_password, command))
    #             LOG.debug('trim silence, response = ' + str(p))
    #
    #             command = 'chown root:root ' + audio_file.split('.')[0]
    #             LOG.debug('trim silence, command 2 = ' + command)
    #             q = os.system('echo %s|sudo -S %s' % (sudo_password, command))
    #             LOG.debug('trim silence, response 2 = ' + str(q))
    #             # self.emitter.emit(Message("css.emit", {"event": "audio source update",
    #             #                                       "data": [get_shout_id_from_filename(audio_file),
    #             #                                                audio_file.split('.')[0]]}))
    #             self.emitter.emit("recognizer_loop.server_response",
    #                               {"event": "audio source update",
    #                                "data": [get_shout_id_from_filename(audio_file),
    #                                         audio_file.split('.')[0]]})
    #
    #             try:
    #                 LOG.info(f"GD: audio.frame_data = {len(audio.frame_data)}")
    #                 # audiofile = self.transcription_service.write_transcribed_files(audio.frame_data, utterance,
    #                 #                                                                nick, nano)
    #                 LOG.info(f"GD: Audio file returned from Transcribe = {audiofile}")
    #                 LOG.info(f"GD: Audio file returned trim silence = {audio_file}")
    #             except Exception as x:
    #                 LOG.error(x)
    #                 audiofile = audio_file
    #
    #         # Only continue if shout has text
    #         if utterance == 'Spoken:':
    #             LOG.warning(f"Ignoring audio input: {utterance}")
    #         else:
    #             audio = None  # there are already utterances, no need for stt.
    #
    #             if nano == "mobile":
    #                 mobile = True
    #                 client = "mobile"
    #             else:
    #                 mobile = False
    #                 if nano:
    #                     client = "nano"
    #                 else:
    #                     client = "klatchat"
    #
    #             # Transcribe().write_transcribed_files(None, utterances, user=nick)
    #
    #             stopwatch = Stopwatch()
    #
    #             ident = str(stopwatch.timestamp) + str(hash(utterance))
    #
    #             # STT succeeded, send the transcribed speech on for processing
    #             # self.get_nick_profiles(text_filename)
    #             self.update_profile_for_nick(nick)
    #             chat_user = self.chat_user_dict.get(nick, None)
    #             stt_language = chat_user.get('stt_language', 'en')
    #             tts_language = chat_user.get('tts_language', 'en-us')
    #             tts_secondary_language = chat_user.get('secondary_tts_language', 'en-us')
    #             LOG.debug('tts language = ' + tts_language)
    #             LOG.debug('tts secondary language = ' + tts_secondary_language)
    #             LOG.debug('stt language = ' + stt_language)
    #             sentence = utterance.lower()
    #             payload = {
    #                 "utterances": [re.sub('^@neon ', '', sentence.rstrip(), flags=re.IGNORECASE)],
    #                 "lang": stt_language,
    #                 "session": SessionManager.get().session_id,
    #                 "ident": ident,
    #                 "user": nick,
    #                 "mobile": mobile,
    #                 "client": client,
    #                 "flac_filename": text_filename,
    #                 "nick_profiles": self.get_nick_profiles(text_filename),
    #                 "neon_should_respond": sentence.lower().startswith("@neon "),
    #                 "cc_data": {"speak_execute": sentence.rstrip(),
    #                             # "audio_file": audio_file,
    #                             "audio_file": audiofile,  # This should be in chat_audio
    #                             "raw_utterance": utterance
    #                             }
    #             }
    #             if payload.get("utterances")[0].startswith('<span style="white-space:pre">script:'):
    #                 LOG.warning("Ignoring script upload!")
    #             else:
    #                 LOG.debug(f'Emitting incoming: {payload.get("utterances")[0]}')
    #                 self.emitter.emit("recognizer_loop:utterance", payload)
    #
    #     except Exception as x:
    #         LOG.info('''  error == ''' + str(x))
    #     finally:
    #
    #         if utterance != 'Spoken:':
    #             # audio shout really
    #             ensure_directory_exists(self.shouts_folder, "shouts_text")
    #             # Transcribe().check_dir("shouts_text/")
    #
    #             mv_to_directory = " " + self.shouts_folder + "shouts_text/"
    #
    #             try:
    #
    #                 LOG.info(''' username = ''' + pwd.getpwuid(os.getuid()).pw_name)
    #                 command = 'mv ' + str(text_filename) \
    #                           + mv_to_directory \
    #                           + os.path.basename(str(text_filename))
    #                 p = os.system(command)
    #                 LOG.info('''move command == ''' + str(command))
    #                 LOG.info('''move command return == ''' + str(p))
    #             except Exception as x:
    #                 LOG.error('''move command error == ''' + str(x))
    #         else:
    #             try:
    #                 p = os.system('rm ' + str(text_filename))
    #                 LOG.info('''remove text file command return == ''' + str(p))
    #             except Exception as x:
    #                 LOG.error('error removing text_filename...' + str(text_filename))
    #                 LOG.error(x)
    #     return text_filename, audio

    # @staticmethod
    # def _get_nicks_for_shout_conversation(filename) -> list:
    #     """
    #     Gets a list of nicknames for the given shout and requesting nick
    #     :param filename: NickInfo file
    #     :return: list of nicks associated with the passed filename
    #     """
    #     nick = get_chat_nickname_from_filename(filename)
    #     shout_id = get_shout_id_from_filename(filename)
    #     nick_filename = get_most_recent(
    #         '/var/www/html/klatchat/app/files/shout_text/cid-' + shout_id + '-*' + nick + '-NickInfo.txt')  # .92
    #     LOG.debug(' get_nicks, nick_filename = ' + str(nick_filename))
    #     if nick_filename:
    #         nicks_to_return = json.load(open(nick_filename))
    #         LOG.debug(nicks_to_return)
    #     else:
    #         nicks_to_return = [nick]
    #     return nicks_to_return

    @staticmethod
    def _build_entry_for_nick(nick: str) -> dict:
        chat_user = ChatUser(nick)
        try:
            LOG.info(chat_user)
            user_profile_settings = {
                "brands": {
                    'ignored_brands': chat_user.brands_ignored,
                    'favorite_brands': chat_user.brands_favorite,
                    'specially_requested': chat_user.brands_requested,
                },
                "user": {
                    'first_name': chat_user.first_name,
                    'middle_name': chat_user.middle_name,
                    'last_name': chat_user.last_name,
                    'preferred_name': chat_user.nick,
                    'full_name': " ".join([name for name in (chat_user.first_name,
                                                             chat_user.middle_name,
                                                             chat_user.last_name) if name]),
                    'dob': chat_user.birthday,
                    'age': chat_user.age,
                    'email': chat_user.email,
                    'username': nick,
                    'password': chat_user.password,
                    'picture': chat_user.avatar,
                    'about': chat_user.about,
                    'phone': chat_user.phone,
                    'email_verified': chat_user.email_verified,
                    'phone_verified': chat_user.phone_verified
                },
                "location": {
                    'lat': chat_user.location_lat,
                    'lng': chat_user.location_long,
                    'city': chat_user.location_city,
                    'state': chat_user.location_state,
                    'country': chat_user.location_country,
                    'tz': chat_user.location_tz,
                    'utc': chat_user.location_utc
                },
                "units": {
                    'time': chat_user.time_format,
                    'date': chat_user.date_format,
                    'measure': chat_user.unit_measure
                },
                "speech": {
                 'stt_language': chat_user.stt_language,
                 'stt_region': chat_user.stt_region,
                 'alt_languages': ['en'],
                 'tts_language': chat_user.tts_language,
                 'tts_gender': chat_user.tts_gender,
                 'neon_voice': chat_user.ai_speech_voice,
                 'secondary_tts_language': chat_user.tts_secondary_language,
                 'secondary_tts_gender': chat_user.tts_secondary_gender,
                 'secondary_neon_voice': '',
                 'speed_multiplier': chat_user.speech_rate
                 # 'synonyms': chat_user.synonyms
                },
                "skills": {i.get("skill_id"): i for i in chat_user.skill_settings}
            }
        except Exception as e:
            LOG.error(e)
            user_profile_settings = None
        return user_profile_settings

    def update_profile_for_nick(self, nick: str):
        if nick not in self.chat_user_dict:
            self.chat_user_dict[nick] = self._build_entry_for_nick(nick)

    def get_nick_profiles(self, nicks: list):
        """
        Updates self.chatUserDict with all users in the conversation associated with the passed filename
        :param nicks: list of nicks in conversation
        """
        # nicks = self._get_nicks_for_shout_conversation(filename)
        # LOG.info('shout_id = '+str(shout_id))
        if not isinstance(nicks, list):
            raise TypeError("Expected list of nicks")
        nicks_in_conversation = dict()
        for nickname in nicks:
            if nickname == "neon":
                LOG.debug("Ignoring neon")
            elif nickname in self.chat_user_dict:
                nicks_in_conversation[nickname] = self.chat_user_dict.get(nickname, None)
                LOG.debug('profile in cache: ' + nickname + ', cache length = ' + str(len(self.chat_user_dict)))
            else:
                # chat_user = ChatUser(nickname)
                try:
                    # LOG.info(chat_user)
                    self.chat_user_dict[nickname] = self._build_entry_for_nick(nickname)
                    LOG.info(self.chat_user_dict[nickname])
                    nicks_in_conversation[nickname] = self.chat_user_dict[nickname]
                    LOG.info(nicks_in_conversation[nickname])
                except Exception as x:
                    LOG.error(x)
                finally:
                    LOG.debug(f'profile added to cache: {nickname} cache length = {len(self.chat_user_dict)}')

        return nicks_in_conversation

    def remove_cached_profile(self, message):
        """
        Handler to remove a cached nick profile when a profile is updated.
        This may be called when a skill or external source changes a user profile
        :param message: Message associated with request
        """
        LOG.debug(f"DM: remove_cache_entry called message={message.data}")
        # LOG.debug(message.data)
        nick = message.data.get("nick", "")  # This IS data, not context
        if not nick:
            LOG.error("Invalid remove cache entry request")
            nick = message.data
        self.chat_user_dict.pop(nick)
