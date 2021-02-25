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

from NGI.utilities.configHelper import *
from mycroft.util.log import LOG
from datetime import date
from datetime import datetime
import time
import subprocess
import requests
from bs4 import BeautifulSoup

# from mycroft.device import device
# if device != 'server':
try:
    import tkinter
    from tkinter import *
    from tkinter import ttk
except Exception as e:
    LOG.error(e)


# Draws Settings Window with Specified Tabs
class PreferencesWindow:

    def __init__(self, pages=None):
        if pages is None:
            pages = ['user', 'device', 'lang', 'wifi', 'control', 'advanced']
        start_time = time.time()
        # Define Window
        self.root = tkinter.Tk()
        self.user_config = NGIConfig("ngi_user_info").content
        self.local_config = NGIConfig("ngi_local_conf").content
        self.icon = PhotoImage(file=self.local_config["dirVars"]["ngiDir"] + '/icons/neon.gif')
        self.root.title("Neon AI Settings")
        self.root.tk.call('wm', 'iconphoto', self.root._w, self.icon)
        self.nb = ttk.Notebook(self.root)
        self.user_page = ttk.Frame(self.nb)
        self.lang_page = ttk.Frame(self.nb)
        self.wifi_page = ttk.Frame(self.nb)
        self.advanced_page = ttk.Frame(self.nb)
        self.control_page = ttk.Frame(self.nb)
        self.device_page = ttk.Frame(self.nb)

        # self.user_config = dict(load_yaml_file(user_info_path))
        # self.local_config = dict(load_yaml_file(configuration_file_path))

        # Initialize YML Keys
        self.first_name = StringVar(value=self.user_config['user']['first_name'])
        self.middle_name = StringVar(value=self.user_config['user']['middle_name'])
        self.last_name = StringVar(value=self.user_config['user']['last_name'])
        self.preferred_name = StringVar(value=self.user_config['user']['preferred_name'])
        self.email = StringVar(value=self.user_config['user']['email'])
        self.username = StringVar(value=self.user_config['user']['username'])
        self.password = StringVar(value=self.user_config['user']['password'])
        self.name = {
            'First Name': self.first_name,
            'Middle Name': self.middle_name,
            'Last Name': self.last_name,
            'Preferred Name': self.preferred_name
        }

        self.dob = StringVar(value=self.user_config['user']['dob'])
        self.dob.set('YYYY/MM/DD') if not self.dob.get() else self.dob
        self.age = StringVar(value=self.user_config['user']['age'])
        self.birth_year = StringVar(value=self.dob.get().split('/')[0])
        self.birth_month = StringVar(value=self.dob.get().split('/')[1])
        self.birth_day = StringVar(value=self.dob.get().split('/')[2])

        self.ssid = StringVar()
        self.psk = StringVar()
        self.wifi = self.user_config['wifi']

        self.units = StringVar(value=self.user_config['units']['measure'])
        self.time = IntVar(value=self.user_config['units']['time'])
        self.date = StringVar(value=self.user_config['units']['date'])
        self.unit_opts = ['imperial', 'metric']
        self.time_opts = [12, 24]
        self.date_opts = ['MDY', 'YMD', 'YDM']

        self.show_debug = BooleanVar(value=self.user_config['interface']['display_neon_brain'])
        self.clapper_on = BooleanVar(value=self.user_config['interface']['clap_commands_enabled'])
        self.wake_words = BooleanVar(value=self.user_config['interface']['wake_words_enabled'])
        self.dialog_opt = BooleanVar(value=self.user_config['interface']['random_dialog_enabled'])
        self.confirm_on = BooleanVar(value=self.user_config['interface']['confirm_listening'])
        self.listen_off = BooleanVar(value=self.user_config['interface']['mute_on_listen'])
        self.ui_toggles = {
            'Show Thinking': self.show_debug,
            'Clap Commands': self.clapper_on,
            'Use Wake Words': self.wake_words,
            'Use Dialog Options': self.dialog_opt,
            'Chime on Wake Word': self.confirm_on,
            'Mute on Wake Word': self.listen_off
        }

        self.stt_lang = StringVar(value=self.user_config['speech']['stt_language'])
        self.stt_reg = StringVar(value=self.user_config['speech']['stt_region'])
        self.alt_langs = list(self.user_config['speech']['alt_languages'])
        self.tts_lang = StringVar(value=self.user_config['speech']['tts_language'])
        self.tts_gender = StringVar(value=self.user_config['speech']['tts_gender'])
        self.tts_lang_2 = StringVar(value=self.user_config['speech']['secondary_tts_language'])
        self.tts_gender_2 = StringVar(value=self.user_config['speech']['secondary_tts_gender'])
        self.speech_multiplier = DoubleVar(value=self.user_config['speech']['speed_multiplier'])
        self.stt_dict = self.local_config['sttOpts']
        self.tts_dict = dict((key.lower(), val.lower()) for key, val in dict(self.local_config['ttsOpts']).items())
        try:
            self.tmp_stt_lang = StringVar(value=list(self.stt_dict.keys())[list(self.stt_dict.values()).
                                          index(self.stt_lang.get() + '-' + self.stt_reg.get())])
            self.tmp_tts_lang = StringVar(value=list(self.tts_dict.keys())[list(self.tts_dict.values()).
                                          index(self.tts_lang.get())])
            self.tmp_tts_lang_2 = StringVar(value=list(self.tts_dict.keys())[list(self.tts_dict.values()).
                                            index(self.tts_lang_2.get())])
        except Exception as x:
            LOG.error("Failed to Get Current Languages")
            self.tmp_tts_lang = StringVar()
            self.tmp_tts_lang_2 = StringVar()
            LOG.error(x)

        self.wake_word = StringVar(value=self.user_config['listener']['wake_word'])
        self.phonetic = StringVar(value=self.user_config['listener']['phonemes'])
        self.rate = IntVar(value=self.user_config['listener']['rate'])
        self.channels = IntVar(value=self.user_config['listener']['channels'])
        self.threshold = IntVar(value=self.user_config['listener']['threshold'])
        self.multiplier = IntVar(value=self.user_config['listener']['multiplier'])
        self.der = DoubleVar(value=self.user_config['listener']['der'])
        self.standup_word = StringVar(value=self.user_config['listener']['standup_word'])
        self.grammar = StringVar(value=self.user_config['listener']['grammar'])
        self.phoneme_duration = IntVar(value=self.user_config['listener']['phoneme_duration'])
        self.module = StringVar(value=self.user_config['listener']['module'])
        self.listen_lang = StringVar(value=self.user_config['listener']['language'])

        self.ww_setting = {
            'Wake Word': self.wake_word
        }
        self.ww_advanced = {
            'Rate': self.rate,
            'Channels': self.channels,
            'Threshold': self.threshold,
            'Multiplier': self.multiplier,
            'Dynamic Energy Ratio': self.der,
            'Standup Word': self.standup_word,
            'Grammar': self.grammar,
            'Phoneme Duration': self.phoneme_duration,
            'Module': self.module,
            'language': self.listen_lang
        }
        self.speech_advanced = {
            'Rate of Speech': self.speech_multiplier
        }

        self.lat = StringVar(value=self.user_config['location']['lat'])
        self.lng = StringVar(value=self.user_config['location']['lng'])
        self.city = StringVar(value=self.user_config['location']['city'])
        self.state = StringVar(value=self.user_config['location']['state'])
        self.country = StringVar(value=self.user_config['location']['country'])
        self.tz = StringVar(value=self.user_config['location']['tz'])
        self.utc = StringVar(value=self.user_config['location']['utc'])
        self.location_settings = {
            'City': self.city,
            'State': self.state,
            'Country': self.country
        }

        self.mac = self.user_config['device']['mac']
        self.ip4 = self.user_config['device']['ip4']
        self.ip6 = self.user_config['device']['ip6']
        self.ver = self.user_config['device']['ver']
        self.dev_info = {
            'MAC Address': self.mac,
            'IPv4 Address': self.ip4,
            'IPv6 Address': self.ip6,
            'Last User Update': self.ver
        }

        self.core_git = StringVar(value=self.local_config['remoteVars']['coreGit'])
        self.core_branch = StringVar(value=self.local_config['remoteVars']['coreBranch'])
        self.skills_git = StringVar(value=self.local_config['remoteVars']['skillsGit'])
        self.skills_branch = StringVar(value=self.local_config['remoteVars']['skillsBranch'])
        self.git_settings = {
            'Core Git': self.core_git,
            'Core Branch': self.core_branch,
            'Skills Git': self.skills_git,
            'Skills Branch': self.skills_branch
        }

        self.remote_skills = StringVar(value=self.local_config['remoteVars']['remoteSkills'])
        self.remote_core = StringVar(value=self.local_config['remoteVars']['remoteCore'])
        self.remote_settings = {
            'Remote Core': self.remote_core,
            'Remote Skills': self.remote_skills
        }

        self.remote_user = StringVar(value=self.local_config['remoteVars']['remoteUser'])
        self.remote_host = StringVar(value=self.local_config['remoteVars']['remoteHost'])
        # self.remote_coupons = StringVar(value=self.local_config['remoteVars']['remoteCoupons'])
        # self.diags_upload = StringVar(value=self.local_config['remoteVars']['diagsUpload'])
        self.email_upload = StringVar(value=self.local_config['remoteVars']['emailUpload'])
        # self.signal_upload = StringVar(value=self.local_config['remoteVars']['signalUpload'])
        self.attachment_upload = StringVar(value=self.local_config['remoteVars']['attachmentUpload'])
        self.remote_advanced = {
            'Remote Host': self.remote_host,
            'Remote User': self.remote_user,
            # 'Remote Coupons': self.remote_coupons,
            # 'Diagnostic Uploads': self.diags_upload,
            'Email Uploads': self.email_upload,
            # 'Signal Uploads': self.signal_upload,
            'Attachment Uploads': self.attachment_upload
        }

        self.auto_start = BooleanVar(value=self.local_config['prefFlags']['autoStart'])
        self.auto_update = BooleanVar(value=self.local_config['prefFlags']['autoUpdate'])
        self.dev_mode = BooleanVar(value=self.local_config['prefFlags']['devMode'])
        self.show_demo = BooleanVar(value=self.local_config['prefFlags']['showDemo'])
        self.device_toggles = {
            'Auto Start': self.auto_start,
            'Auto Update': self.auto_update,
            'Developer Mode': self.dev_mode,
            'Demo Mode': self.show_demo
        }

        self.oh_host = StringVar(value=self.local_config['homeControl']['openhabHost'])
        self.oh_port = StringVar(value=self.local_config['homeControl']['openhabPort'])
        self.oh_conf = StringVar(value=self.local_config['homeControl']['openhabConf'])
        self.oh_settings = {
            'openHAB Server': self.oh_host,
            'openHAB Port': self.oh_port,
            'openHAB Configuration': self.oh_conf
        }

        self.code_source = StringVar(value=self.local_config['prefFlags']['codeSource'])
        self.source_settings = {'Code Source': ['ngi', 'git']}

        # Refresh OH Configuration
        # HomeHelpers.update_home_yml()
        self.home_dict = NGIConfig("ngi_home_control").content
        LOG.debug(self.home_dict)
        # TODO: Append other dicts here DM
        self.light_dict = self.home_dict['Lighting']['tplinksmarthome']
        self.switch_dict = self.home_dict['Switchable']['tplinksmarthome']
        # for brand in self.home_dict['Lighting']:
        #     try:
        #         print(dict(brand))
        #         self.light_dict.update(dict(brand))
        #     except Exception as e:
        #         print(e)
        # for brand in self.home_dict['Switchable']:
        #     try:
        #         print(dict(brand))
        #         self.light_dict.update(dict(brand))
        #     except Exception as e:
        #         print(e)
        self.switch = StringVar()
        self.new_sw = StringVar()
        self.lights = StringVar()
        self.new_lb = StringVar()

        # old = self.switch.get(), new = textboxVar

        self.timezones = ['-12.0', '-11.0', '-10.0', '-9.5', '-9.0', '-8.0', '-7.0', '-6.0', '-5.0', '-4.0', '-3.0',
                          '-2.5', '-2.0', '-1.0', '0.0', '+1.0', '+2.0', '+3.0', '+3.5', '+4.0', '+4.5', '+5.0', '+5.5',
                          '+5.75', '+6.0', '+6.5', '+7.0', '+8.0', '+8.75', '+9.0', '+9.5', '+10.0', '+10.5', '+11.0',
                          '+12.0', '+13.0', '+13.75', '+14.0']

        self.draw_pages(pages)

        button_block = Frame(self.root)
        tkinter.Button(button_block, text="Submit", command=lambda: self.submit_action()) \
            .pack(side='left', expand=1, fill='both')
        tkinter.Button(button_block, text='Cancel', command=lambda: self.cancel_action()) \
            .pack(side='right', expand='1', fill='both')
        LOG.info(time.time() - start_time)
        self.nb.pack(expand=1, fill='both')
        button_block.pack(expand=1, fill='both')
        self.root.bind('<Return>', self.submit_action)
        self.root.mainloop()
        LOG.debug('Settings init:' + str(time.time() - start_time))

    def cancel_action(self):
        self.root.destroy()

    def submit_action(self):
        start_time = time.time()
        LOG.info(self.user_config)
        LOG.info(self.local_config)
        self.wifi[self.ssid.get()] = self.psk.get()
        LOG.info(self.wifi)

        # Update Device Info
        self.ip4, self.ip6, self.mac = LookupHelpers.get_net_info()
        self.ver = str(datetime.now())

        # Update Password if Changed
        if self.password.get() != self.user_config['user']['password']:
            self.password.set(LookupHelpers.encrypt(self.password.get()))

        # Update dob and age if changed
        if self.birth_year.get() != 'YYYY':
            self.dob.set(str(self.birth_year.get()) + '/' + str(self.birth_month.get()) + '/' +
                         str(self.birth_day.get()))
            if self.dob.get() != self.user_config['user']['dob']:
                LOG.info('New DOB')
                self.age.set(LookupHelpers.get_age(self.birth_year.get(), self.birth_month.get(), self.birth_day.get()))

        # Update time, coordinates if city changed
        if self.city.get() != self.user_config['location']['city']:
            LOG.info('New Location')
            gps_loc = {
                'city': self.city.get(),
                'state': self.state.get(),
                'country': self.country.get()
            }
            lat, lng = LookupHelpers.get_coordinates(gps_loc)
            self.lat.set(lat)
            self.lng.set(lng)
            timezone, offset = LookupHelpers.get_timezone(self.lat.get(), self.lng.get())
            self.tz.set(timezone)
            self.utc.set(offset) if self.utc.get() == self.user_config['location']['utc'] else None

        # Update phoenetics if WW changed
        if self.wake_word.get() != self.user_config['listener']['wake_word']:
            self.phonetic.set(LookupHelpers.get_phonemes(self.wake_word.get()))

        # Update openHab config if changed
        if self.new_sw.get():
            HomeHelpers.oh_rename(self.switch.get(), self.new_sw.get())
        if self.new_lb.get():
            HomeHelpers.oh_rename(self.lights.get(), self.new_lb.get())

        try:
            self.update_dict()
            LOG.info(dict(self.user_config))
            # LOG.info(dict(self.local_config))
            NGIConfig('ngi_user_info').populate(dict(self.user_config))
            NGIConfig('ngi_local_conf').populate(dict(self.local_config))
            # TODO: continue replacement
            #  reload_yaml_file(user_info_path, self.user_config)
            #  NGIConfigig_load.reload_yaml_file(self.conf.configuration_file_path, self.local_config)
            #  create_signal("NGI_YAML_config_update")
            #  self.conf.update_yaml_file(yaml_type='config', header='remoteVars',
            #                             value=self.local_config['remoteVars'], multiple=True)
            #  self.conf.update_yaml_file(yaml_type='config', header='prefFlags',
            #                             value=self.local_config['prefFlags'], multiple=False)
        except Exception as x:
            LOG.info(x)

        self.root.destroy()
        LOG.info(time.time() - start_time)

    def update_dict(self):
        neon_voice_1 = self.local_config[
            'ttsVoice'][self.tts_dict[self.tmp_tts_lang.get()].lower()][self.tts_gender.get()]
        try:
            neon_voice_2 = self.local_config[
                'ttsVoice'][self.tts_dict[self.tmp_tts_lang_2.get()].lower()][self.tts_gender_2.get()]
        except Exception as x:
            LOG.info(x)
            neon_voice_2 = ''
        try:
            updated_user = {
                'first_name': self.first_name.get(),
                'middle_name': self.middle_name.get(),
                'last_name': self.last_name.get(),
                'preferred_name': self.preferred_name.get(),
                'full_name': self.first_name.get() + ' ' + self.middle_name.get() + ' ' + self.last_name.get(),
                'dob': self.dob.get(),
                'age': self.age.get(),
                'email': self.email.get(),
                'username': self.username.get(),
                'password': self.password.get()
            }
            self.user_config['user'] = updated_user

            # self.user_config['wifi'] = self.wifi

            updated_speech = {
                'stt_language': self.stt_dict[self.tmp_stt_lang.get()].split('-')[0],
                'stt_region': self.stt_dict[self.tmp_stt_lang.get()].split('-')[1],
                'alt_languages': self.alt_langs,
                'tts_language': self.tts_dict[self.tmp_tts_lang.get()],
                'tts_gender': self.tts_gender.get(),
                'neon_voice': neon_voice_1,
                'secondary_tts_language': self.tts_dict[self.tmp_tts_lang_2.get()],
                'secondary_tts_gender': self.tts_gender_2.get(),
                'secondary_neon_voice': neon_voice_2,
                'speed_multiplier': self.speech_multiplier.get()
            }
            self.user_config['speech'] = updated_speech

            updated_units = {
                'time': self.time.get(),
                'date': self.date.get(),
                'measure': self.units.get()
            }
            self.user_config['units'] = updated_units

            updated_interface = {
                'display_neon_brain': self.show_debug.get(),
                'clap_commands_enabled': self.clapper_on.get(),
                'wake_words_enabled': self.wake_words.get(),
                'random_dialog_enabled': self.dialog_opt.get(),
                'confirm_listening': self.confirm_on.get(),
                'mute_on_listen': self.listen_off.get()
            }
            self.user_config['interface'] = updated_interface

            updated_listener = {
                'wake_word': self.wake_word.get(),
                'phonemes': self.phonetic.get(),
                'rate': self.rate.get(),
                'channels': self.channels.get(),
                'threshold': self.threshold.get(),
                'multiplier': self.multiplier.get(),
                'der': self.der.get(),
                'standup_word': self.standup_word.get(),
                'grammar': self.grammar.get(),
                'phoneme_duration': self.phoneme_duration.get(),
                'dev_index': None,
                'module': self.module.get(),
                'language': self.listen_lang.get()
            }
            self.user_config['listener'] = updated_listener

            updated_location = {
                'lat': self.lat.get(),
                'lng': self.lng.get(),
                'city': self.city.get(),
                'state': self.state.get(),
                'country': self.country.get(),
                'tz': self.tz.get(),
                'utc': self.utc.get()
            }
            self.user_config['location'] = updated_location

            updated_device = {
                'mac': self.mac,
                'ip4': self.ip4,
                'ip6': self.ip6,
                'ver': self.ver
            }
            self.user_config['device'] = updated_device
        except Exception as x:
            LOG.error(x)
        try:
            updated_remote = {
                'coreGit': self.core_git.get(),
                'coreBranch': self.core_branch.get(),
                'skillsGit': self.skills_git.get(),
                'skillsBranch': self.skills_branch.get(),
                'remoteUser': self.remote_user.get(),
                'remoteHost': self.remote_host.get(),
                'remoteCore': self.remote_core.get(),
                'remoteSkills': self.remote_skills.get(),
                # 'remoteCoupons': self.remote_coupons.get(),
                # 'diagsUpload': self.diags_upload.get(),
                'emailUpload': self.email_upload.get(),
                # 'signalUpload': self.signal_upload.get(),
                'attachmentUpload': self.attachment_upload.get()
            }
            self.local_config['remoteVars'] = updated_remote

            updated_prefs = {
                'autoStart': self.auto_start.get(),
                'autoUpdate': self.auto_update.get(),
                'codeSource': self.code_source.get(),
                'devMode': self.dev_mode.get(),
                'showDemo': self.show_demo.get()
            }
            self.local_config['prefFlags'] = updated_prefs

            updated_control = {
                'openhabHost': self.oh_host.get(),
                'openhabPort': self.oh_port.get(),
                'openhabConf': self.oh_conf.get()
            }
            self.local_config['homeControl'] = updated_control

            # self.local_config['devVars'] = dict(self.local_config['devVars'])
            # self.local_config['gnome'] = dict(self.local_config['gnome'])
            # self.local_config['dirVars'] = dict(self.local_config['dirVars'])
            # self.local_config['fileVars'] = dict(self.local_config['fileVars'])
            # self.local_config['authVars'] = dict(self.local_config['authVars'])
            # self.local_config['homeControl'] = dict(self.local_config['homeControl'])
            # self.local_config['ttsVoice'] = dict(self.local_config['ttsVoice'])
            # self.local_config['ttsOpts'] = dict(self.local_config['ttsOpts'])
            # self.local_config['sttOpts'] = dict(self.local_config['sttOpts'])
            # self.local_config['sttSpokenOpts'] = dict(self.local_config['sttSpokenOpts'])

        except Exception as x:
            LOG.error(x)

    def draw_pages(self, pages):
        for page in pages:
            if page == 'user':
                self.draw_user()
                self.nb.add(self.user_page, text='User')
            if page == 'device':
                self.draw_device()
                self.nb.add(self.device_page, text='Device')
            if page == 'lang':
                self.draw_lang()
                self.nb.add(self.lang_page, text='Languages')
            if page == 'control':
                self.draw_control()
                self.nb.add(self.control_page, text='Smart Home')
            if page == 'wifi':
                self.draw_wifi()
                self.nb.add(self.wifi_page, text='Wifi')
            if page == 'advanced':
                self.draw_advanced()
                self.nb.add(self.advanced_page, text='Advanced')

    def draw_user(self):
        ins_row = 0
        WindowHelpers.build_text_entry(parent=self.user_page, fields=self.name, start_row=0, entry_width=16) \
            .grid(row=ins_row, column=0, sticky='NEW', columnspan=4, pady=8)
        ins_row += 1
        WindowHelpers.build_text_entry(parent=self.user_page, fields={'Email Address': self.email}, start_row=1,
                                       entry_width=50).grid(row=ins_row, column=0, sticky='NSEW', columnspan=4, pady=8)
        ins_row += 1
        account_block = Frame(self.user_page)
        WindowHelpers.build_text_entry(parent=account_block, fields={'Klat Username': self.username}, start_row=1,
                                       entry_width=50).grid(row=ins_row, column=0, sticky='NSEW', columnspan=1, pady=8)
        WindowHelpers.obscured_text_entry(parent=account_block, fields={'Klat Password': self.password},
                                          start_row=1, entry_width=50).grid(row=ins_row, column=1,
                                                                            sticky='NSEW', columnspan=1, pady=8)
        account_block.grid_rowconfigure(ins_row, weight=1)
        account_block.grid_columnconfigure(0, weight=1)
        account_block.grid_columnconfigure(1, weight=1)
        account_block.grid(row=ins_row, column=0, sticky='NESW', pady=8)
        ins_row += 1

        bday_block = Frame(self.user_page)
        tkinter.Label(bday_block, text='Date of Birth', justify='left').grid(row=ins_row - 1, column=0, sticky='SW')
        WindowHelpers.build_dropdown_entry(parent=bday_block, var=self.birth_year, options=list(range(1919, 2020))) \
            .grid(row=ins_row, column=0, sticky='NSEW')
        WindowHelpers.build_dropdown_entry(parent=bday_block, var=self.birth_month, options=list(range(1, 13))) \
            .grid(row=ins_row, column=1, sticky='NSEW')
        WindowHelpers.build_dropdown_entry(parent=bday_block, var=self.birth_day, options=list(range(1, 32))) \
            .grid(row=ins_row, column=2, sticky='NSEW')
        bday_block.grid(row=ins_row, column=0, sticky='NW', pady=8)
        bday_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 1

        # WindowHelpers.build_text_entry(parent=self.user_page, fields=self.wifi, start_row=0, entry_width=32)\
        #     .grid(row=ins_row, column=0, sticky='NSEW', columnspan=4, pady=8)
        # ins_row += 1
        WindowHelpers.build_text_entry(parent=self.user_page, fields=self.location_settings, start_row=0,
                                       entry_width=24) \
            .grid(row=ins_row, column=0, sticky='NSEW', columnspan=4, pady=8)
        ins_row += 1
        WindowHelpers.build_dropdown_entry(parent=self.user_page, var=self.utc, options=self.timezones) \
            .grid(row=ins_row, column=0, sticky='NW', pady=8)
        ins_row += 1
        WindowHelpers.build_text_entry(parent=self.user_page, fields=self.ww_setting, start_row=0, entry_width=24) \
            .grid(row=ins_row, column=0, sticky='NSEW', columnspan=4, pady=8)
        ins_row += 1
        WindowHelpers.build_radio_selection(parent=self.user_page, var=self.units, opts=self.unit_opts, title='Units') \
            .grid(row=ins_row, column=0, sticky='NW', columnspan=1, pady=8)
        ins_row += 1
        WindowHelpers.build_radio_selection(parent=self.user_page, var=self.time, opts=self.time_opts,
                                            title='Time Format') \
            .grid(row=ins_row, column=0, sticky='NW', columnspan=1)
        ins_row += 1
        WindowHelpers.build_radio_selection(parent=self.user_page, var=self.date, opts=self.date_opts,
                                            title='Date Format') \
            .grid(row=ins_row, column=0, sticky='NW', columnspan=1)
        ins_row += 1
        WindowHelpers.build_check_boxes(parent=self.user_page, fields=self.ui_toggles, width=4) \
            .grid(row=ins_row, column=0, sticky='NSEW', columnspan=2, pady=8)
        ins_row += 1

        # option_block = Frame(self.top)
        # tkinter.Button(option_block, text="Privacy", command=lambda: WindowHelpers.clear_data_window(self.top))\
        #     .grid(row=0, column=0, sticky='NSEW', columnspan=1)
        # tkinter.Button(option_block, text="User Input Language", command=lambda: gui.change_stt(gui)) \
        #     .grid(row=0, column=1, sticky='NSEW', columnspan=1)
        # tkinter.Button(option_block, text="Neon Response Languages", command=lambda: gui.change_tts(gui)) \
        #     .grid(row=0, column=2, sticky='NSEW', columnspan=1)
        # option_block.grid_columnconfigure(0, weight=1)
        # option_block.grid_columnconfigure(1, weight=1)
        # option_block.grid_columnconfigure(2, weight=1)
        # option_block.grid_rowconfigure(1, weight=1)
        # option_block.grid(row=ins_row, column=0, sticky='NSEW', columnspan=4)
        ins_row += 1

        y = 0
        while y <= 2:
            self.user_page.grid_columnconfigure(y, weight=1)
            y += 1
        x = 0
        while x <= ins_row:
            self.user_page.grid_rowconfigure(x, weight=1)
            x += 1

    def draw_device(self):
        ins_row = 0

        source_block = Frame(self.device_page)
        tkinter.Label(source_block, text='Code Source: ') \
            .grid(row=ins_row, column=0, sticky='NSEW', columnspan=1, pady=8)
        WindowHelpers.build_dropdown_entry(source_block, self.code_source, ['ngi', 'git']) \
            .grid(row=ins_row, column=1, sticky='NSEW', columnspan=1, pady=8)
        source_block.grid(row=ins_row, column=0, sticky='NESW', pady=8)
        source_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 1

        remote_block = Frame(self.device_page)
        WindowHelpers.build_text_entry(remote_block, self.remote_settings) \
            .grid(row=ins_row, column=0, sticky='NSEW', columnspan=1, pady=8)
        WindowHelpers.build_text_entry(remote_block, self.git_settings) \
            .grid(row=ins_row + 1, column=0, sticky='NSEW', columnspan=1, pady=8)
        remote_block.grid(row=ins_row, column=0, sticky='NESW', pady=8)
        remote_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 1

        WindowHelpers.build_check_boxes(self.device_page, self.device_toggles, 4) \
            .grid(row=ins_row, column=0, sticky='NSEW', columnspan=1, pady=8)

    def draw_lang(self):
        ins_row = 0

        input_block = Frame(self.lang_page)
        tkinter.Label(input_block, text='User Input Language', justify='left') \
            .grid(row=ins_row, column=0, sticky='SW', columnspan=4)
        WindowHelpers.build_dropdown_entry(input_block, self.tmp_stt_lang, list(self.stt_dict.keys())) \
            .grid(row=ins_row + 1, column=0, sticky='NSEW', columnspan=4)
        input_block.grid(row=ins_row, column=0, sticky='NW', pady=8)
        input_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 1

        output_block = Frame(self.lang_page)
        tkinter.Label(output_block, text='Neon Output Language', justify='left') \
            .grid(row=ins_row, column=0, sticky='SW', columnspan=4)
        WindowHelpers.build_dropdown_entry(output_block, self.tmp_tts_lang, list(self.tts_dict.keys())) \
            .grid(row=ins_row + 1, column=0, sticky='NSEW')
        WindowHelpers.build_radio_selection(output_block, self.tts_gender, ['male', 'female'], ''). \
            grid(row=ins_row + 1, column=1, sticky='NSEW')
        output_block.grid(row=ins_row, column=0, sticky='NW', pady=8)
        output_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 1

        output_block_2 = Frame(self.lang_page)
        tkinter.Label(output_block_2, text='Second Output Language', justify='left') \
            .grid(row=ins_row, column=0, sticky='SW', columnspan=4)
        WindowHelpers.build_dropdown_entry(output_block_2, self.tmp_tts_lang_2, list(self.tts_dict.keys())) \
            .grid(row=ins_row + 1, column=0, sticky='NSEW')
        WindowHelpers.build_radio_selection(output_block_2, self.tts_gender_2, ['male', 'female'], ''). \
            grid(row=ins_row + 1, column=1, sticky='NSEW')
        output_block_2.grid(row=ins_row, column=0, sticky='NW', pady=8)
        output_block_2.grid_rowconfigure(ins_row, weight=1)

        y = 0
        while y <= 2:
            self.user_page.grid_columnconfigure(y, weight=1)
            y += 1
        x = 0
        while x <= ins_row:
            self.user_page.grid_rowconfigure(x, weight=1)
            x += 1

    def draw_wifi(self):
        ins_row = 0

        ssid_block = Frame(self.wifi_page)
        tkinter.Label(ssid_block, text='SSID', justify='left') \
            .grid(row=ins_row, column=0, sticky='SW', columnspan=4)
        WindowHelpers.build_dropdown_entry(parent=self.wifi_page, var=self.ssid, options=list(self.wifi.keys())) \
            .grid(row=ins_row + 1, column=0, sticky='NEW', columnspan=4)
        ssid_block.grid(row=ins_row, column=0, sticky='NW', pady=8)
        ssid_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 2
        WindowHelpers.build_text_entry(self.wifi_page, fields={'Password': self.psk}, entry_width=32) \
            .grid(row=ins_row, column=0, sticky='NW', pady=8)
        y = 0
        while y <= 2:
            self.user_page.grid_columnconfigure(y, weight=1)
            y += 1
        x = 0
        while x <= ins_row:
            self.user_page.grid_rowconfigure(x, weight=1)
            x += 1

    def draw_advanced(self):
        ins_row = 0

        listener_block = Frame(self.advanced_page)
        WindowHelpers.build_text_entry(listener_block, fields=self.ww_advanced, entry_width=8) \
            .grid(row=ins_row, column=0, sticky='NW', pady=8)
        WindowHelpers.build_text_entry(listener_block, fields=self.speech_advanced, entry_width=8) \
            .grid(row=ins_row + 1, column=0, sticky='NW', pady=8)
        listener_block.grid(row=ins_row, column=0, sticky='NW', pady=8)
        listener_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 1
        info_block = Frame(self.advanced_page)
        tkinter.Label(info_block, text='Device Info', justify='left') \
            .grid(row=ins_row, column=0, sticky='SW', columnspan=4)
        tkinter.Label(info_block, text='IP: ' + self.ip4, justify='left') \
            .grid(row=ins_row + 1, column=0, sticky='SW', columnspan=4)
        tkinter.Label(info_block, text='IPv6: ' + self.ip6, justify='left') \
            .grid(row=ins_row + 2, column=0, sticky='SW', columnspan=4)
        tkinter.Label(info_block, text='MAC: ' + self.mac, justify='left') \
            .grid(row=ins_row + 3, column=0, sticky='SW', columnspan=4)
        tkinter.Label(info_block, text='Last Update: ' + self.ver, justify='left') \
            .grid(row=ins_row + 4, column=0, sticky='SW', columnspan=4)
        info_block.grid(row=ins_row, column=0, sticky='NW', pady=8)
        info_block.grid_rowconfigure(ins_row, weight=1)

        y = 0
        while y <= 2:
            self.user_page.grid_columnconfigure(y, weight=1)
            y += 1
        x = 0
        while x <= ins_row:
            self.user_page.grid_rowconfigure(x, weight=1)
            x += 1

    def draw_control(self):
        ins_row = 0

        rename_block = Frame(self.control_page)
        tkinter.Label(rename_block, text='Switch') \
            .grid(row=ins_row, column=0, sticky='SW', columnspan=1)
        WindowHelpers.build_dropdown_entry(rename_block, self.switch, list(self.switch_dict.keys())) \
            .grid(row=ins_row, column=1, sticky='SW', columnspan=1)
        WindowHelpers.build_text_entry(rename_block, {'New Name': self.new_sw}) \
            .grid(row=ins_row, column=2, sticky='SW', columnspan=1)
        tkinter.Label(rename_block, text='Light') \
            .grid(row=ins_row + 1, column=0, sticky='SW', columnspan=1)
        WindowHelpers.build_dropdown_entry(rename_block, self.lights, list(self.light_dict.keys())) \
            .grid(row=ins_row + 1, column=1, sticky='SW', columnspan=1)
        WindowHelpers.build_text_entry(rename_block, {'New Name': self.new_lb}) \
            .grid(row=ins_row + 1, column=2, sticky='SW', columnspan=1)
        # tkinter.Label(rename_block, text='Switches', justify='left') \
        #     .grid(row=ins_row, column=0, sticky='SW', columnspan=1)
        # WindowHelpers.build_vertical_text_entry(rename_block, self.switches) \
        #     .grid(row=ins_row + 1, column=0, sticky='NSEW', columnspan=1)
        # tkinter.Label(rename_block, text='Lights', justify='left') \
        #     .grid(row=ins_row, column=1, sticky='SW', columnspan=1)
        # WindowHelpers.build_vertical_text_entry(rename_block, self.lights) \
        #     .grid(row=ins_row + 1, column=1, sticky='NSEW', columnspan=1)
        rename_block.grid(row=ins_row, column=0, sticky='NW', pady=8)
        rename_block.grid_rowconfigure(ins_row, weight=1)
        ins_row += 1
        WindowHelpers.build_text_entry(self.control_page, self.oh_settings) \
            .grid(row=ins_row, column=0, sticky='SW', columnspan=1)

        y = 0
        while y <= 2:
            self.user_page.grid_columnconfigure(y, weight=1)
            y += 1
        x = 0
        while x <= ins_row:
            self.user_page.grid_rowconfigure(x, weight=1)
            x += 1


# Static Methods for Drawing in tK
class WindowHelpers:

    # Build Frame of Vertically Titled Text Entry
    @staticmethod
    def build_text_entry(parent, fields, start_row=0, start_column=0, column_span=1, entry_width=None):
        block = Frame(parent)
        y = start_column
        x = start_row
        for label, field in fields.items():
            textfield = tkinter.Label(block, text=label, justify='left')
            textfield.grid(row=x, column=y, sticky='SW', columnspan=column_span, pady=0)
            textfield = tkinter.Entry(block, textvariable=field, width=entry_width)
            textfield.grid(row=x + 1, column=y, sticky='NSEW', columnspan=column_span, pady=0)
            block.grid_columnconfigure(y, weight=1)
            y += column_span
        block.grid_rowconfigure(x, weight=1)
        return block

    # Build Frame of Horizontally Titled Text Entry
    @staticmethod
    def build_vertical_text_entry(parent, fields, start_row=0, start_column=0, column_span=1, entry_width=None):
        block = Frame(parent)
        y = start_column
        x = start_row
        for label, field in fields.items():
            textfield = tkinter.Label(block, text=label, justify='left')
            textfield.grid(row=x, column=y, sticky='SW', columnspan=column_span, pady=0)
            textfield = tkinter.Entry(block, textvariable=field, width=entry_width)
            textfield.grid(row=x, column=y + 1, sticky='NSEW', columnspan=column_span, pady=0)
            block.grid_columnconfigure(y, weight=1)
            x += 1
        block.grid_rowconfigure(x, weight=1)
        return block

    # Build Frame of Horizontal Titled Obscured Text Entry
    @staticmethod
    def obscured_text_entry(parent, fields, start_row=0, start_column=0, column_span=1, entry_width=None):
        block = Frame(parent)
        y = start_column
        x = start_row
        for label, field in fields.items():
            textfield = tkinter.Label(block, text=label, justify='left')
            textfield.grid(row=x, column=y, sticky='SW', columnspan=column_span, pady=0)
            textfield = tkinter.Entry(block, textvariable=field, show='*', width=entry_width)
            textfield.grid(row=x + 1, column=y, sticky='NSEW', columnspan=column_span, pady=0)
            block.grid_columnconfigure(y, weight=1)
            y += column_span
        block.grid_rowconfigure(x, weight=1)
        return block

    # Build Frame of Horizontal Radio Buttons
    @staticmethod
    def build_radio_selection(parent, var, opts, title='Title'):
        block = Frame(parent)
        tkinter.Label(block, text=title, justify='left').grid(row=0, column=0, sticky='W')
        x = 0
        y = 1
        for opt in opts:
            # Draw Gender Selection Buttons
            btn = Radiobutton(block, text=opt, variable=var, value=opt,
                              command=lambda o=opt: var.set(o))
            btn.grid(row=x, column=y, sticky='W')
            if var.get() == opt:
                btn.invoke()
                block.grid_columnconfigure(y, weight=1)
            y += 1
        block.grid_rowconfigure(x, weight=1)
        return block

    # Build Frame of Horizontal Checkboxes
    @staticmethod
    def build_check_boxes(parent, fields, width=2):
        block = Frame(parent)
        # tkinter.Label(block, text=title, justify='center').grid(row=0, column=0, sticky='NESW')
        y = 0
        x = 0
        for label, field in fields.items():
            if y == width:
                block.grid_rowconfigure(x, weight=1)
                x += 1
                y = 0
            checkbox = Checkbutton(block, text=label, variable=field, command=lambda o=field: LOG.info(o.get()))
            checkbox.grid(row=x, column=y, sticky='NW')
            block.grid_columnconfigure(y, weight=1)
            y += 1
        block.grid_rowconfigure(x, weight=1)
        return block

    # Build Frame with Single Dropdown
    @staticmethod
    def build_dropdown_entry(parent, var, options):
        block = Frame(parent)
        # tkinter.Label(block, text=title, justify='center').grid(row=0, column=0, sticky='NESW')
        ttk.Combobox(block, textvariable=var, values=options).grid(row=0, column=0)
        return block

    # Build Frame of Vertical Buttons
    @staticmethod
    def build_buttons(parent, fields, height=5):
        block = Frame(parent)
        x = 0
        y = 0
        for field in fields:
            if x == height:
                block.grid_columnconfigure(y, weight=1)
                x = 0
                y += 1
            button = Button(block, text=field,
                            command=lambda o=field: WindowHelpers.return_button(parent, o))
            button.grid(row=x, column=y, sticky='NSEW')
            block.grid_rowconfigure(x, weight=1)
            x += 1
        block.grid_columnconfigure(y, weight=1)
        return block

    # Generic Window of Buttons
    @staticmethod
    def build_buttons_window(parent, title, fields, height=5):
        popup = Toplevel(parent)
        icon = PhotoImage(file=NGIConfig("ngi_local_conf").content["dirVars"]["ngiDir"] + '/icons/neon.gif')
        popup.title(title)
        popup.tk.call('wm', 'iconphoto', parent._w, icon)
        WindowHelpers.build_buttons(popup, fields, height).grid(row=0, column=0)
        popup.lift()
        popup.mainloop()

    # TODO: return value
    @staticmethod
    def return_button(window, opt):
        LOG.info(opt)
        window.destroy()

    # Generic Window with Text Entry
    @staticmethod
    def build_entry_window(parent, title, variable):
        popup = Toplevel(parent)
        icon = PhotoImage(file=NGIConfig("ngi_local_conf").content["dirVars"]["ngiDir"] + '/icons/neon.gif')
        popup.title('Enter ' + title)
        popup.tk.call('wm', 'iconphoto', parent, icon)
        WindowHelpers.build_text_entry(popup, {title: variable}).grid(row=0, column=0, sticky='NEWS')
        button_block = Frame(popup)
        tkinter.Button(button_block, text="Submit",
                       command=lambda: WindowHelpers.return_button(popup, variable.get()))\
            .pack(side='left', expand=1, fill='both')
        tkinter.Button(button_block, text='Cancel', command=lambda: popup.destroy()) \
            .pack(side='right', expand='1', fill='both')

        popup.lift()
        popup.mainloop()

    # Generic Window with options to clear data
    @staticmethod
    def clear_data_window(parent):
        popup = Toplevel(parent)
        # self.icon = PhotoImage(file=self.local_config["dirVars"]["ngiDir"]+'/icons/neon.gif')
        popup.title("Privacy")
        # self.top.tk.call('wm', 'iconphoto', self.top._w, self.icon)
        likes = BooleanVar(value=False)
        trans = BooleanVar(value=False)
        media = BooleanVar(value=False)
        prefs = BooleanVar(value=False)
        langs = BooleanVar(value=False)
        cache = BooleanVar(value=False)
        profile = BooleanVar(value=False)
        user = BooleanVar(value=False)

        data_toggles = {
            'Likes': likes,
            'Transcriptions': trans,
            'Pictures and Videos': media,
            'Preferences': prefs,
            'Languages': langs,
            'Cached Responses': cache,
            'User Info': user,
            'Complete Profile': profile
        }
        WindowHelpers.build_check_boxes(parent=popup, fields=data_toggles, width=3) \
            .grid(row=0, column=0, sticky='NSEW', columnspan=2)
        submit = tkinter.Button(popup, text="Clear Selected", command=lambda: WindowHelpers.clear_data_helper(
            data_toggles, popup))
        cancel = tkinter.Button(popup, text='Cancel', command=lambda: popup.destroy())
        submit.grid(row=1, column=0, sticky='NSEW', columnspan=1)
        cancel.grid(row=1, column=1, sticky='NSEW', columnspan=1)
        popup.lift()
        popup.mainloop()

    # Helper Method for clear_data_window
    @staticmethod
    def clear_data_helper(options, window=None):
        # import subprocess
        opts = []
        LOG.debug(options)
        # info = self.conf.user_info_path
        data_commands = {
            'Likes': 'b',
            'Transcriptions': 't',
            'Pictures and Videos': 'p',
            'Preferences': 'r',
            'Languages': 'l',
            'Cached Responses': 'c',
            'Complete Profile': 'a',
            'User Info': 'u',
            'Selected Transcripts': 's',
            'Ignored Transcripts': 'i'
        }
        for key, value in options.items():
            if value.get():
                opts.append(data_commands.get(key))
        NeonHelpers.clear_data(opts, window)

    # Draw Window with Diagnostic options
    @staticmethod
    def send_diags_window(parent):
        popup = Toplevel(parent)
        # self.icon = PhotoImage(file=self.local_config["dirVars"]["ngiDir"]+'/icons/neon.gif')
        popup.title("Send Diagnostics")
        # self.top.tk.call('wm', 'iconphoto', self.top._w, self.icon)

        opt = StringVar()
        diags_opt = Radiobutton(popup, text="Limited Logs (No Personal Information)", variable=opt, value=None,
                                command=lambda: opt.set(''))
        logs_opt = Radiobutton(popup, text="Logs with Transcriptions", variable=opt, value='l',
                               command=lambda: opt.set('l'))
        audio_opt = Radiobutton(popup, text="Logs with Transcriptions and Audio", variable=opt, value='a',
                                command=lambda: opt.set('a'))
        submit = tkinter.Button(popup, text="Submit", command=lambda: WindowHelpers.send_diags(popup, opt))
        cancel = tkinter.Button(popup, text='Cancel', command=lambda: popup.destroy())

        diags_opt.grid(row=0, column=0, columnspan=2)
        logs_opt.grid(row=1, column=0, columnspan=2)
        audio_opt.grid(row=2, column=0, columnspan=2)
        submit.grid(row=3, column=1)
        cancel.grid(row=3, column=0)

    # Sends Logs Selected in send_diags_menu
    @staticmethod
    def send_diags(window, opt):
        import os
        LOG.debug(opt.get())
        os.system("gnome-terminal -- " + NGIConfig("ngi_local_conf").content['dirVars']['ngiDir'] +
                  "/shortcuts/upload.sh -" + opt.get())
        window.destroy()


# Static Methods for simple value lookups
class LookupHelpers:

    # Accepts location dict and returns str lat, lng
    @staticmethod
    def get_coordinates(gps_loc):
        from geopy.geocoders import Nominatim
        coordinates = Nominatim(user_agent="neon-ai")
        try:
            location = coordinates.geocode(gps_loc)
            LOG.debug(f"{location}")
            return location.latitude, location.longitude
        except Exception as x:
            LOG.error(x)
            return -1, -1

    # Accepts lat, lng string or float and returns str city, state, country
    @staticmethod
    def get_location(lat, lng):
        from geopy.geocoders import Nominatim
        address = Nominatim(user_agent="neon-ai")
        location = address.reverse([lat, lng], language="en-US")
        LOG.debug(f"{location}")
        LOG.debug(f"{location.raw}")
        LOG.debug(f"{location.raw.get('address')}")
        city = location.raw.get('address').get('city')
        county = location.raw.get('address').get('county')
        state = location.raw.get('address').get('state')
        country = location.raw.get('address').get('country')
        return city, county, state, country

    # get_location With pickle lookup
    #     LOG.debug("DM: get_location called")
    #     start_time = time.time()
    #     import pickle
    #     config = NGIConfig("ngi_local_conf").content
    #     loc_cache = config["dirVars"]["cacheDir"] + "/location"
    #     loc_dict = None
    #     locations = dict()
    #
    #     # Try to open and read cache file to get address associated with coordinates
    #     if isfile(loc_cache):
    #         LOG.debug("DM: cache exists")
    #         with open(loc_cache, 'rb') as cached_locations:
    #             try:
    #                 locations = pickle.load(cached_locations)
    #                 if f"{lat}, {lng}" in locations:
    #                     loc_dict = locations[f"{lat}, {lng}"]
    #             except Exception as e:
    #                 LOG.error(e)
    #                 loc_dict = None
    #
    #     if loc_dict:
    #         LOG.debug(f"DM: cached location time={time.time() - start_time}")
    #         return loc_dict["city"], loc_dict["state"], loc_dict["country"]
    #     else:
    #         LOG.debug("DM: new location lookup")
    #         from geopy.geocoders import Nominatim
    #         address = Nominatim()
    #         location = address.reverse([lat, lng])
    #         locations[f"{lat}, {lng}"] = location.raw.get('address')
    #         city = location.raw.get('address').get('city')
    #         state = location.raw.get('address').get('state')
    #         country = location.raw.get('address').get('country')
    #
    #         with open(loc_cache, 'wb+') as cached_locations:
    #             # Write out new cache
    #             pickle.dump(locations, cached_locations)
    #         LOG.debug(f"DM: lookup location time={time.time() - start_time}")
    #         return city, state, country

    # Accepts str or float lat, lng and returns str timezone name, hours offset
    @staticmethod
    def get_timezone(lat, lng):
        from timezonefinder import TimezoneFinder as Tf
        import pendulum
        timezone = Tf().timezone_at(lng=float(lng), lat=float(lat))
        offset = pendulum.from_timestamp(0, timezone).offset_hours
        return timezone, offset

    # Accepts a timezone name and returns the hours offset
    @staticmethod
    def get_offset(timezone):
        from pendulum import from_timestamp
        return from_timestamp(0, timezone).offset_hours

    # Accepts str year, month, day and returns int age
    @staticmethod
    def get_age(year, month='1', day='1'):
        # TODO: Update this to use the same method as personal skill DM
        age = date.today().year - int(year) - ((date.today().month, date.today().day) < (int(month), int(day)))
        return age

    # Accepts str phrase and returns str phonemes
    @staticmethod
    def get_phonemes(phrase):
        import nltk
        import re

        try:
            nltk.download('cmudict')
            output = ''
            for word in phrase.split():
                phoenemes = nltk.corpus.cmudict.dict()[word.lower()][0]

                for phoeneme in phoenemes:
                    output += str(re.sub('[0-9]', '', phoeneme) + ' ')
                output += '. '
            return output.rstrip()
        except Exception as x:
            LOG.debug(x)
            nltk.download('cmudict')

    # Returns Device MAC Address
    @staticmethod
    def get_net_info():
        import netifaces
        default_dev = netifaces.gateways()['default'][netifaces.AF_INET][1]
        mac = netifaces.ifaddresses(default_dev)[netifaces.AF_LINK][0]['addr']
        ip4 = netifaces.ifaddresses(default_dev)[netifaces.AF_INET][0]['addr']
        ip6 = netifaces.ifaddresses(default_dev)[netifaces.AF_INET6][0]['addr']
        return ip4, ip6, mac

    # Returns list of available script files
    @staticmethod
    def get_scripts_list():
        cc_skill_dir = NGIConfig("ngi_local_conf").content["dirVars"]["skillsDir"] + "/custom-conversation.neon"
        available = [os.path.splitext(x)[0].replace("_", " ") for x in os.listdir(f'{cc_skill_dir}/script_txt/')
                     if os.path.isfile(os.path.join(f'{cc_skill_dir}/script_txt', x))]
        LOG.info(available)
        return available

    # Encrypts Data
    @staticmethod
    def encrypt(plaintext):
        from Crypto.Cipher import AES

        key = NGIConfig("ngi_local_conf").content['dirVars']['coreDir'].encode('utf-16')[0:32]
        cipher = AES.new(key, AES.MODE_EAX, key)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-16'))
        encrypted = list(ciphertext)
        return encrypted

    # Decrypts Data
    @staticmethod
    def decrypt(encrypted_text):
        from Crypto.Cipher import AES

        encrypted = bytes(encrypted_text)
        key = NGIConfig("ngi_local_conf").content['dirVars']['coreDir'].encode('utf-16')[0:32]
        cipher = AES.new(key, AES.MODE_EAX, key)
        output = cipher.decrypt(encrypted)
        return output.decode('utf-16')


# Wrapper functions for BASH functions
class OSHelpers:

    # Displays Local Neon Helpfile in default browser
    @staticmethod
    def show_help():
        import webbrowser
        webbrowser.open('file://' + NGIConfig("ngi_local_conf").content['dirVars']['ngiDir'] + '/neonHelp.html')

    # Installs and runs TeamViewer Remote Access Software
    @staticmethod
    def get_support():
        subprocess.Popen(['gnome-terminal', '--title=Neon Support', '--',
                          NGIConfig("ngi_local_conf").content['dirVars']['ngiDir'] + '/shortcuts/support.sh'])

    # Displays Neon Demo Presentation and Test
    @staticmethod
    def show_demo():
        subprocess.Popen(['gnome-terminal', '--title=Neon AI Demo Tour', '--',
                          NGIConfig("ngi_local_conf").content['dirVars']['ngiDir'] + '/shortcuts/demoNeon.sh'])

    # Opens Test Selection Window
    @staticmethod
    def test_neon():
        subprocess.Popen(['gnome-terminal', '--title=Neon Testing', '--',
                          NGIConfig("ngi_local_conf").content['dirVars']['ngiDir'] + '/shortcuts/testNeon.sh'])

    # Checks for Updates and Installs
    @staticmethod
    def update_action():
        create_signal("DCC_initiateUpdate")
        subprocess.Popen(['gnome-terminal', '--title=Neon Update', '--',
                          'sudo', f"{NGIConfig('ngi_local_conf').content['dirVars']['ngiDir']}/update.sh"])  # | "
        # f"tee -a {NGIConfig('ngi_local_conf').content['dirVars']['logsDir']}/update.log'"])


# Static Methods for Home Control
class HomeHelpers:
    # Callable class to detect and add new Wemo Devices
    class WemoSetup:
        def __init__(self):
            from ouimeaux.environment import Environment
            self.switches = []
            # self.conf = NGIConfig()
            env = Environment(self.on_switch)
            env.start()
            env.discover(seconds=5)
            for switch in self.switches:
                dev_id = str(switch)
                model = 'socket'
                name = "New Wemo Plug " + dev_id[-4:]
                if str('Socket-1_0-' + dev_id) not in \
                        NGIConfig("ngi_home_control").content['Switchable']['wemo'].values():
                    HomeHelpers.write_openhab(binding_id='wemo', type_id=model, label=name.lower(), name=name,
                                              parameters=['udn="Socket-1_0-' + dev_id + '"'])

        def on_switch(self, switch):
            print(switch.metainfo.GetMetaInfo()['MetaInfo'].split('|')[1])
            self.switches.append(switch.metainfo.GetMetaInfo()['MetaInfo'].split('|')[1])

    # Finds TPLink Devices on the Network
    @staticmethod
    def get_tp_id():
        # import nmap
        import json
        import ipaddress
        from NGI.utilities.controlsHelper import tp_connect
        # from elevate import elevate
        # nm = nmap.PortScanner()
        ip4, ip6, mac = LookupHelpers.get_net_info()
        net = ipaddress.ip_network(ip4 + '/255.255.255.0', strict=False)
        # nm.scan(hosts='192.168.165.0/24', arguments='-p 9999')
        # elevate()
        # nm.scan('192.168.165.0/24', '9999', '-sU')
        subnet = ipaddress.ip_network(net)

        # LOG.debug(nm.all_hosts())
        dev_ip_list = {}
        for host in subnet:
            LOG.debug(host)
            # print(nm.hostname)
            try:
                result = tp_connect('{"system":{"get_sysinfo":null}}', host)
                if result:
                    result = json.loads(result)
                    tp_id = result['system']['get_sysinfo']['deviceId']
                    tp_type = result['system']['get_sysinfo']['model'][:5].lower()
                    dev_ip_list[tp_id] = tp_type
            except Exception as x:
                LOG.debug(x)
                LOG.debug('Not a TPLink Device')
                pass
        LOG.debug(dev_ip_list)
        return dev_ip_list

    # Writes openHab Thing and Item line for a given device
    @staticmethod
    def write_openhab(binding_id, type_id, name, label=None, location=None, parameters=None):
        import datetime
        n = name.replace(' ', '').lower()
        if location:
            string = binding_id + ':' + type_id + ':' + n + ' "' + label + '" @ "' + location + '" ' + str(parameters)
        else:
            string = binding_id + ':' + type_id + ':' + n + ' "' + label + '" ' + str(parameters)

        items_line = None
        kind = None
        if 'hs' in type_id:
            kind = 'Switchable'
            items_line = 'Switch TP_Sw_' + n + ' "' + name + '" ["Switchable"] { channel="' + binding_id + \
                         ':' + type_id + ':' + n + ':switch" }'
        elif 'lb110' in type_id:
            kind = 'Lighting'
            items_line = 'Dimmer TP_LB_' + n + ' "' + name + '" ["Lighting"] { channel="' + binding_id + \
                         ':' + type_id + ':' + n + ':brightness" }'
        elif 'lb120' in type_id:
            kind = 'Lighting'
            items_line = 'Dimmer TP_LB_' + n + ' "' + name + '" ["Lighting"] { channel="' + binding_id + \
                         ':' + type_id + ':' + n + ':brightness" }\n' \
                                                   'Dimmer TP_LB_TEMP_' + n + ' "' + name + \
                         ' Temperature" ["Lighting"] { channel="' + \
                         binding_id + ':' + type_id + ':' + n + ':colorTemperature" }'
        elif 'socket' in type_id:
            kind = 'Switchable'
            items_line = 'Switch Wemo_Sw_' + n + ' "' + name + '" ["Switchable"] { channel="' + binding_id + \
                         ':' + type_id + ':' + n + ':state" }'
        thing_line = string.replace("'", "")
        try:
            # LOG.debug(str(self.local_config['homeControl']['openhabConf'] + '/things/' +
            #                        binding_id + '.things'))
            thing_file = open(NGIConfig("ngi_local_conf").content['homeControl']['openhabConf'] +
                              '/things/' + binding_id + '.things', 'a+')
            # LOG.debug(str(thing_file))
            things = thing_file.readlines()
            # LOG.debug(str(things))
            # LOG.debug(str(parameters).replace("'", ""))
            write_line = True
            for line in things:
                # LOG.debug(str(line))
                if str(parameters).replace("'", "") in line:
                    write_line = False
            if write_line:
                thing_file.write('\n' + thing_line)
                thing_file.close()
                items_file = open(NGIConfig("ngi_local_conf").content['homeControl']['openhabConf'] +
                                  '/items/' + binding_id + '.items', 'a+')
                # LOG.debug(str(items_file))
                # LOG.debug(str(items_line))
                items_file.write('\n' + items_line)
                items_file.close()
            else:
                thing_file.close()
        except Exception as x:
            LOG.error(x)

        try:
            conf = NGIConfig("ngi_home_control")
            home_dict = conf.content[kind][binding_id]
            home_dict[name] = str(parameters[0].split('"')[1])
            # create_signal("NGI_YAML_home_update")
            conf.update_yaml_file('info', 'last_update', str(datetime.datetime.now()), True)
            conf.update_yaml_file(kind, binding_id, home_dict, True, True)
        except Exception as x:
            LOG.error('Failed to Update YML: ' + str(x))
            # LOG.error(home_dict)

    # # Encrypts JSON Strings for TPLink
    # @staticmethod
    # def tp_encrypt(string):
    #     key = 171
    #     result = b"\0\0\0" + bytes([len(string)])
    #     for i in bytes(string.encode('latin-1')):
    #         a = key ^ i
    #         key = a
    #         result += bytes([a])
    #     return result
    #
    # # Decrypts JSON Strings from TPLink
    # @staticmethod
    # def tp_decrypt(string):
    #     key = 171
    #     result = b""
    #     for i in bytes(string):
    #         a = key ^ i
    #         key = i
    #         result += bytes([a])
    #     return result.decode('latin-1')

    # # Connects to and Communicates with TPLink Devices
    # @staticmethod
    # def tp_connect(commands, ip='192.168.0.1', port=9999, timeout=0.2):
    #     # Changes Copyright 2018 Neongecko Inc. | All Rights Reserved
    #     # Copyright 2016 softScheck GmbH
    #     #
    #     # Licensed under the Apache License, Version 2.0 (the "License");
    #     # you may not use this file except in compliance with the License.
    #     # You may obtain a copy of the License at
    #     #
    #     #      http://www.apache.org/licenses/LICENSE-2.0
    #     #
    #     # Unless required by applicable law or agreed to in writing, software
    #     # distributed under the License is distributed on an "AS IS" BASIS,
    #     # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    #     # See the License for the specific language governing permissions and
    #     # limitations under the License.
    #     import socket
    #     # Send command and receive reply
    #     try:
    #         LOG.debug(commands)
    #         start_time = time.time()
    #         socket.setdefaulttimeout(timeout)
    #         sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         sock_tcp.connect((str(ip), int(port)))
    #         sock_tcp.send(HomeHelpers.tp_encrypt(commands))
    #         data = sock_tcp.recv(2048)
    #         sock_tcp.close()
    #         LOG.debug('DM: Discover Time: ' + str(time.time() - start_time))
    #         LOG.debug(HomeHelpers.tp_decrypt(data[4:]))
    #         result = HomeHelpers.tp_decrypt(data[4:])
    #         return result
    #
    #     except socket.error:
    #         LOG.debug("Cound not connect to host " + str(ip) + ":" + str(port))

    # Renames openHab Thing and Item, updates yml
    @staticmethod
    def oh_rename(old_name, new_name):
        import os
        import re
        config = NGIConfig("ngi_local_conf").content
        old_name = old_name.lower()
        new_name = new_name.replace('-', ' ')
        for things_file in os.listdir(config['homeControl']['openhabConf'] + '/things'):
            with open(config['homeControl']['openhabConf'] + '/things/' + things_file, 'r+') as things:
                things_data = things.read()
                things_data = re.sub(str('"' + old_name + '"'), str('"' + new_name + '"'), things_data,
                                     flags=re.IGNORECASE)
                things_data = things_data.replace(old_name.replace(' ', ''), new_name.lower().replace(' ', ''))
                # things_data = things_data.replace(old_name, new_name)
                # things_data = things_data.replace(old_name.replace(' ', ''), new_name.replace(' ', ''))
            with open(config['homeControl']['openhabConf'] + '/things/' + things_file, 'w+') as things:
                things.write(things_data)
        for items_file in os.listdir(config['homeControl']['openhabConf'] + '/items'):
            with open(config['homeControl']['openhabConf'] + '/items/' + items_file, 'r+') as items:
                items_data = items.read()
                items_data = re.sub(str('"' + old_name + '"'), str('"' + new_name + '"'), items_data,
                                    flags=re.IGNORECASE)
                items_data = items_data.replace(old_name.replace(' ', ''), new_name.lower().replace(' ', ''))
                # items_data = items_data.replace(old_name, new_name)
                # items_data = items_data.replace(old_name.replace(' ', ''), new_name.replace(' ', ''))
            with open(config['homeControl']['openhabConf'] + '/items/' + items_file, 'w+') as items:
                items.write(items_data)

        home_control_path = NGIConfig("ngi_home_control").file_path
        with open(home_control_path, 'r+') as yml:
            conf_data = yml.read()
            conf_data = conf_data.replace(old_name, new_name)
        with open(home_control_path, 'w+') as yml:
            yml.write(conf_data)

    # Detects and Configures New TPLink Devices on Network
    @staticmethod
    def tp_setup():
        import os.path
        all_tp = HomeHelpers.get_tp_id()
        for tp_id, tp_type in all_tp.items():
            # tp_id = HomeHelpers.tp_get_id(ip)
            LOG.debug(tp_id)
            name = 'New TPLink ' + tp_type + ' ' + tp_id[-4:]
            if not os.path.isfile(NGIConfig("ngi_local_conf").content['homeControl']['openhabConf'] +
                                  '/things/tplinksmarthome.things') \
                    or tp_id not in open(NGIConfig("ngi_local_conf").content['homeControl']['openhabConf'] +
                                         '/things/tplinksmarthome.things').read():
                if 'hs' in tp_type:
                    # NGIConfig().home_info_available['switches']['tp_link'][name] = tp_id
                    HomeHelpers.write_openhab(binding_id='tplinksmarthome', type_id=tp_type, label=name.lower(),
                                              name=name, parameters=['deviceId="' + tp_id + '"', 'refresh=60'])
                if 'lb' in tp_type:
                    # NGIConfig().home_info_available['lights']['tp_link'][name] = tp_id
                    HomeHelpers.write_openhab(binding_id='tplinksmarthome', type_id=tp_type, label=name.lower(),
                                              name=name, parameters=['deviceId="' + tp_id + '"', 'refresh=60',
                                                                     'transitionPeriod=1500'])
        HomeHelpers.update_home_yml()

    # Writes changes in openHab configs to YML
    @staticmethod
    def update_home_yml():
        import datetime
        import os

        conf = NGIConfig("ngi_local_conf").content
        home_dict = NGIConfig("ngi_home_control").content

        for things_file in os.listdir(conf['homeControl']['openhabConf'] + '/things'):
            if things_file != 'readme.txt:':
                try:
                    binding = os.path.splitext(os.path.basename(things_file))[0]
                    print(binding)
                    devices = {}
                    items_file = open(conf['homeControl']['openhabConf'] +
                                      '/items/' + binding + '.items', 'r')
                    things_file = open(conf['homeControl']['openhabConf'] +
                                       '/things/' + binding + '.things', 'r')

                    for line in things_file.readlines():
                        try:
                            dev_name = line.split('"')[1]
                            dev_id = line.split('"')[3]
                            devices[dev_name] = dev_id
                        except IndexError:
                            LOG.debug('Non-Things Line in ' + str(things_file.name) + ' ' + str(line))
                        except Exception as x:
                            LOG.error(x)
                    for name, ident in devices.items():
                        for line in items_file.readlines():
                            if name in line.lower():
                                kind = line.split('"')[3]
                                name = line.split('"')[1]
                                home_dict[kind][binding][name] = ident
                        items_file.seek(0)
                    items_file.close()
                    things_file.close()
                    print(home_dict)
                    home_dict['info']['last_update'] = str(datetime.datetime.now())
                except Exception as x:
                    LOG.error(x)
        # reload_yaml_file(home_info_path, home_dict)

    # Calls all methods to add devices
    @staticmethod
    def scan_devices():
        try:
            HomeHelpers.WemoSetup()
        except Exception as x:
            LOG.error(x)
        try:
            HomeHelpers.tp_setup()
        except Exception as x:
            LOG.error(x)


# Static Methods for Interacting with NeonAI
class NeonHelpers:
    # Disables Wake Words
    @staticmethod
    def disable_ww():
        # import os
        # from time import sleep
        LOG.info('Disabling Wake Words')
        conf = NGIConfig("ngi_local_conf")
        # create_signal("NGI_YAML_user_update")
        NGIConfig("ngi_user_info").update_yaml_file("interface", "wake_words_enabled", False)

        if not check_for_signal('CORE_skipWakeWord', -1):
            create_signal('CORE_skipWakeWord')
            subprocess.call(['bash', '-c', conf.content['dirVars']['coreDir'] + "/start_neon.sh voice"])
            # os.system("sudo -H -u " + conf.content['devVars']['installUser'] + ' ' +
            #           conf.content['dirVars']['coreDir'] + "/start_neon.sh voice")
            # self.conf.create_signal('restartedFromSkill')
            # self.conf.create_signal("Intent_overwrite_req")
            # sleep(5)
            # os.system("sudo -H -u " + self.local_config['devVars']['installUser'] + ' ' +
            #           self.local_config['dirVars']['ngiDir'] + "/utilities/skip_ww_default.sh")
            # sleep(2)
            # os.system("sudo -H -u " + self.local_config['devVars']['installUser'] + ' ' +
            #           self.local_config['dirVars']['coreDir'] + "/start_neon.sh skills")

    # Enables Wake Words
    @staticmethod
    def enable_ww():
        # import os
        # from time import sleep
        LOG.info('Enabling Wake Words')
        conf = NGIConfig("ngi_local_conf")
        # create_signal("NGI_YAML_user_update")

        NGIConfig("ngi_user_info").update_yaml_file("interface", "wake_words_enabled", True)
        if check_for_signal('CORE_skipWakeWord'):
            check_for_signal("CORE_streamToSTT")
            subprocess.call(['bash', '-c', conf.content['dirVars']['coreDir'] + "/start_neon.sh voice"])
            # os.system("sudo -H -u " + conf.content['devVars']['installUser'] + ' ' +
            #           conf.content['dirVars']['coreDir'] + "/start_neon.sh voice")
            # check_for_signal("Intent_overwrite_req")
            # check_for_signal('skip_wake_word')
            # check_for_signal('startListening')
            # create_signal('restartedFromSkill')
            # sleep(5)
            # os.system("sudo -H -u " + NGIConfig().configuration_available['devVars']['installUser'] + ' ' +
            #           NGIConfig().configuration_available['dirVars']['ngiDir'] + "/utilities/ww_default.sh")
            # sleep(2)
            # os.system("sudo -H -u " + self.local_config['devVars']['installUser'] + ' ' +
            #           self.local_config['dirVars']['coreDir'] + "/start_neon.sh skills")

    # Speaks Using Polly
    @staticmethod
    def polly_say(text, voice='Joanna'):
        # TODO: Handle language, audio streams, mute while speaking DM
        import os
        # import pulsectl
        import boto3
        import logging

        try:
            user = NGIConfig("ngi_user_info").content
            # pulse = pulsectl.Pulse('Mycroft-audio-service')
            conf = user['tts']['amazon']
            # print(conf)
            access_key = conf.get('aws_access_key_id')
            secret_key = conf.get('aws_secret_access_key')
            region = conf.get('region')
            logging.getLogger('boto').setLevel(logging.CRITICAL)
            resp = boto3.client(service_name='polly',
                                region_name=region,
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key).synthesize_speech(OutputFormat='mp3',
                                                                                    Text=text,
                                                                                    VoiceId=voice)
            speak_file = open("/tmp/speak.mp3", 'wb')
            sound_bytes = resp['AudioStream'].read()
            speak_file.write(sound_bytes)
            speak_file.close()
            # for sink in pulse.sink_input_list():
            #     try:
            #         # LOG.debug('sink: ' + str(sink))
            #         volume = sink.volume
            #         if sink.name == "neon-voice":
            #             # Ensures neon-voice volume is 100%
            #             volume.value_flat = 1.0
            #             pulse.volume_set(sink, volume)
            #     except Exception as e:
            #         print(e)
            #         pass
            os.system('mpv --volume=100 --audio-client-name=neon-voice ' + str(speak_file.name) + ">/dev/null")
            os.remove(str(speak_file.name))
        except Exception as x:
            LOG.error(x)

    @staticmethod
    def clear_data(opts, window=None):
        config = NGIConfig("ngi_user_info")
        for opt in opts:
            if opt == 'b' or opt == 'a':
                # create_signal("NGI_YAML_user_update")
                # config.update_yaml_file("brands", "ignored_brands", [], True)
                # config.update_yaml_file("brands", "favorite_brands", [], True)
                # config.update_yaml_file("brands", "popular_brands", [], True)
                # config.update_yaml_file("brands", "specially_requested", [])
                config.populate({'brands': {'ignored_brands': {},
                                            'favorite_brands': {},
                                            'specially_requested': {}}
                                 })
            if opt == 'r' or opt == 'a':
                # NGIConfigig_load.update_yaml_file("speech", "tts_gender", 'female')
                # NGIConfigig_load.update_yaml_file("speech", "tts_language", 'en-US')
                # NGIConfigig_load.update_yaml_file("speech", "neon_voice", 'Joanna')
                # NGIConfigig_load.update_yaml_file("speech", "secondary_tts_language", 'none')
                # NGIConfigig_load.update_yaml_file("speech", "secondary_tts_gender", 'none')
                # NGIConfigig_load.update_yaml_file("speech", "secondary_neon_voice", 'none')
                # NGIConfigig_load.update_yaml_file("speech", "stt_language", 'en')
                # NGIConfigig_load.update_yaml_file("speech", "stt_region", 'US')
                # NGIConfigig_load.update_yaml_file("speech", "alt_languages", ['en'])
                # create_signal("NGI_YAML_user_update")
                # config.update_yaml_file("units", "time", '12', True)
                # config.update_yaml_file("units", "measure", 'imperial', True)
                # config.update_yaml_file("interface", "display_neon_brain", True, True)
                # config.update_yaml_file("interface", "clap_commands_enabled", False, True)
                # config.update_yaml_file("interface", "wake_words_enabled", False, True)
                # config.update_yaml_file("interface", "random_dialog_enabled", False, True)
                # config.update_yaml_file("interface", "confirm_listening", False, True)
                # config.update_yaml_file("listener", "wake_word", 'Hey Neon', True)
                # config.update_yaml_file("listener", "phonemes", 'HH E Y . N IY AA N .', True)
                # config.update_yaml_file("listener", "standup_word", 'wake up', True)
                # config.update_yaml_file("listener", "grammar", 'lm', True)
                # config.update_yaml_file("listener", "rate", 16000, True)
                # config.update_yaml_file("listener", "channels", 1, True)
                # config.update_yaml_file("listener", "threshold", 1e-20, True)
                # config.update_yaml_file("listener", "multiplier", 1, True)
                # config.update_yaml_file("listener", "der", 1.25, True)
                # config.update_yaml_file("listener", "phoneme_duration", 120, True)
                # config.update_yaml_file("listener", "dev_index", None, True)
                # config.update_yaml_file("listener", "module", 'pocketsphinx', True)
                # config.update_yaml_file("listener", "language", 'en-us')
                config.populate({'units': {'time': '12',
                                           'measure': 'impreial'},
                                 'interface': {"display_neon_brain": True,
                                               "clap_commands_enabled": False,
                                               "wake_words_enabled": False,
                                               "random_dialog_enabled": False,
                                               "confirm_listening": False},
                                 'listener': {"wake_word": 'Hey Neon',
                                              "phonemes": 'HH E Y . N IY AA N .',
                                              "standup_word": 'wake up',
                                              "grammar": 'lm',
                                              "rate": 16000,
                                              "channels": 1,
                                              "threshold": 1e-20,
                                              "multiplier": 1,
                                              "der": 1.25,
                                              "phoneme_duration": 120,
                                              "dev_index": None,
                                              "module": 'pocketsphinx',
                                              "language": 'en-us'}
                                 })
            if opt == 'l' or opt == 'a':
                # create_signal("NGI_YAML_user_update")
                # config.update_yaml_file("speech", "tts_gender", 'female', True)
                # config.update_yaml_file("speech", "tts_language", 'en-US', True)
                # config.update_yaml_file("speech", "neon_voice", 'Joanna', True)
                # config.update_yaml_file("speech", "secondary_tts_language", '', True)
                # config.update_yaml_file("speech", "secondary_tts_gender", '', True)
                # config.update_yaml_file("speech", "secondary_neon_voice", '', True)
                # config.update_yaml_file("speech", "stt_language", 'en', True)
                # config.update_yaml_file("speech", "stt_region", 'US', True)
                # config.update_yaml_file("speech", "speed_multiplier", 1, True)
                # config.update_yaml_file("speech", "alt_languages", ['en'])
                config.populate({'speech': {"tts_gender": 'female',
                                            "tts_language": 'en-US',
                                            "neon_voice": 'Joanna',
                                            "secondary_tts_language": '',
                                            "secondary_tts_gender": '',
                                            "secondary_neon_voice": '',
                                            "stt_language": 'en',
                                            "stt_region": 'US',
                                            "speed_multiplier": 1,
                                            "alt_languages": ['en']}
                                 })
            if opt == 'u' or opt == 'a':
                # create_signal("NGI_YAML_user_update")
                # config.update_yaml_file("user", "first_name", '', True)
                # config.update_yaml_file("user", "middle_name", '', True)
                # config.update_yaml_file("user", "last_name", '', True)
                # config.update_yaml_file("user", "preferred_name", '', True)
                # config.update_yaml_file("user", "full_name", '', True)
                # config.update_yaml_file("user", "dob", 'YYYY/MM/DD', True)
                # config.update_yaml_file("user", "age", '', True)
                # config.update_yaml_file("user", "email", '', True)
                # config.update_yaml_file("user", "username", '', True)
                # config.update_yaml_file("user", "password", '', True)
                # config.update_yaml_file("user", "picture", '')
                config.populate({'user': {"first_name": '',
                                          "middle_name": '',
                                          "last_name": '',
                                          "preferred_name": '',
                                          "full_name": '',
                                          "dob": 'YYYY/MM/DD',
                                          "age": '',
                                          "email": '',
                                          "username": '',
                                          "password": '',
                                          "picture": ''}
                                 })

            subprocess.call(['bash', '-c', ". " + NGIConfig("ngi_local_conf").content["dirVars"]["ngiDir"]
                             + "/functions.sh; refreshNeon -" + opt])
        if window:
            window.destroy()

    @staticmethod
    def get_audio(username, string_to_find, return_all=False):
        """
        Get an audio filename for the passed utterance text associated with the given username
        :param: username: Username to search (Preferred for SDK, nick for Server)
        :param: string_to_find: Utterance to search for
        :param: return_all: Boolean return a list of matches or only first match
        """
        import glob
        LOG.debug(f"Find audio: {string_to_find} for {username}")
        audio_dir = NGIConfig("ngi_local_conf").content["dirVars"]["docsDir"] + f"/ts_transcripts_audio_segments"
        files = [f for f in glob.glob(f"{audio_dir}/{username}-*/*") if f.endswith(string_to_find)]
        LOG.debug(f"found {files}")
        if return_all:
            return files
        else:
            # TODO: Sort and return newest
            return files[0]


"""Auto-Complete Domain Algorithm"""


def return_close_values(source_dict, to_find, num_of_return, typo_check=True):
    fin_res = []
    from collections import Counter
    import operator
    if not to_find:
        return []
    if " " in to_find:
        for i in to_find.split(" "):
            fin_res.extend(_return_close_values(source_dict, i, num_of_return, typo_check))
        LOG.debug(fin_res)
        tmp_f = Counter(fin_res)
        LOG.debug(tmp_f)
        tmp = sorted(tmp_f.items(), key=operator.itemgetter(1), reverse=True)
        LOG.debug(tmp)
        return [i for i, m in tmp][:num_of_return]
    return _return_close_values(source_dict, to_find, num_of_return, typo_check)


def _return_close_values(source_dict, to_find, num_of_return, typo_check=True):
    import difflib
    allow_diffs = 1  # if len(to_find) < 4 else 2

    perfect_match = [i for i, v in source_dict.items() if (isinstance(v, str) and to_find == v)
                     or (isinstance(v, list) and [x for x in v if to_find == x])]
    contains_in = [k for k, i in source_dict.items() if to_find in i or (isinstance(i, str) and i in to_find)
                   or (isinstance(i, list) and [x for x in i if x in to_find or to_find in x])]
    close_match = list(set(k for c in difflib.get_close_matches(to_find, source_dict.values())
                           for k, v in source_dict.items() if v == c))

    def check_diffs(i, k):
        len_i = len(i)
        len_tf = len(to_find)
        if abs(len_i - len_tf) > allow_diffs:
            return
        counter_i, counter_tf = 0, 0
        diff_count = 0
        while counter_i < len_i and counter_tf < len_tf:
            if to_find[counter_tf] != i[counter_i]:
                diff_count += 1
                if diff_count > allow_diffs:
                    break
                if len_tf > len_i:
                    counter_tf += 1
                elif len_i > len_tf:
                    counter_i += 1
                else:
                    counter_i += 1
                    counter_tf += 1
            else:
                counter_i += 1
                counter_tf += 1

        if diff_count <= allow_diffs:
            typos_check.append(k)

    typos_check = []
    if typo_check:
        for k, i in source_dict.items():
            if isinstance(i, str):
                check_diffs(i, k)
            elif isinstance(i, list):
                for x in i:
                    if k not in typos_check:
                        check_diffs(x, k)

    LOG.debug(f"perfect match - {perfect_match}")
    LOG.debug(f'contains part - {contains_in}')
    LOG.debug(f"close_match - {close_match}")
    if typo_check:
        LOG.debug(f"typo check {allow_diffs} characters diff - {typos_check}")

    if not close_match and not contains_in and not perfect_match and not typos_check:
        return []
    try:
        res_tmp = typos_check
        res_tmp.extend([i for i in close_match if i not in typos_check])
        res_tmp.extend([i for i in contains_in if i not in close_match])
        LOG.debug(f'res_tmp is {res_tmp}')
    except Exception as x:
        LOG.debug(x)
        res_tmp = []

    if perfect_match:
        if len(perfect_match) == num_of_return:
            return perfect_match
        else:
            need_add = num_of_return - len(perfect_match)
            LOG.debug(len(perfect_match))
            LOG.debug(need_add)
            if need_add < 0:
                return perfect_match[:num_of_return]

            res = perfect_match
            if res_tmp:
                res.extend([i for i in res_tmp if i not in perfect_match])
                LOG.debug(res)
    else:
        res = res_tmp

    return res[:num_of_return] if res else ValueError


# can be changed in the future. yaml options?
headers_Get = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


# to use for the product search and question results if others fail.
# may be replaced with https://developers.google.com/custom-search/docs/tutorial/creatingcse
def google_results_search(q):
    s = requests.Session()
    q = '+'.join(q.split())
    url = 'https://www.google.com/search?q=' + q + '&ie=utf-8&oe=utf-8'
    r = s.get(url, headers=headers_Get)

    soup = BeautifulSoup(r.text, "html.parser")
    output = {}
    # print(soup)
    for searchWrapper in soup.find_all('div', {'class': 'r'}):
        url = searchWrapper.find('a')["href"]
        print(url)
        text = searchWrapper.find('h3').text.strip()
        print(text)
        output[text] = url
    print(output)
    return output


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if str(sys.argv[1]) == 'eww':
            NeonHelpers.enable_ww()
        elif str(sys.argv[1]) == 'sww':
            NeonHelpers.disable_ww()
        elif str(sys.argv[1]) == 'prefs' and NGIConfig("ngi_local_conf").content["devVars"]["devType"] != 'server':
            PreferencesWindow()
        elif str(sys.argv[1]) == 'speak':
            NeonHelpers.polly_say(str(sys.argv[2]))
        else:
            LOG.debug('utilHelper called with no argument')

    # # Returns TPLink deviceID from IP
    # @staticmethod
    # def tp_get_id(ip):
    #     import json
    #     result = HomeHelpers.tp_connect('{"system":{"get_sysinfo":null}}', ip)
    #     result = json.loads(result)
    #     result = result['system']['get_sysinfo']['deviceId']
    #     print(result)
    #     return result
