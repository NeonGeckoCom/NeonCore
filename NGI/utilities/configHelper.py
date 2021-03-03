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

import json
import os
import time
import shutil
from copy import deepcopy
from os.path import dirname, isfile
from os.path import join
from collections import MutableMapping
from contextlib import suppress
from filelock import FileLock
from ruamel.yaml import YAML


"""
Purpose: configHelper is a handler for YAML files, containing saved user's 
         settings and information. YAML files are parsed and read into 
         dictionaries for future processing. 
         
         All skills have access to update_yaml_file.
         
         new_yaml_file, load_yaml_file, reload_yaml_file belong to the
         configHelper logically and are used in NGI bash scripts, in addition
         to the NGIConfig, which is why they are not a part of the 
         class.
"""


def resolve_resource_file(res_name):
    """Convert a resource into an absolute filename.

    Resource names are in the form: 'filename.ext'
    or 'path/filename.ext'

    The system wil look for ~/.neon/res_name first, and
    if not found will look at $dataDir/res_name,
    then finally it will look for res_name in the 'mycroft/res'
    folder of the source code package.

    Example:
    With Neon running as the user 'bob', if you called
        resolve_resource_file('snd/beep.wav')
    it would return either '/home/bob/.neon/snd/beep.wav' or
    '$rootDir/snd/beep.wav' or '.../mycroft/res/snd/beep.wav',
    where the '...' is replaced by the path where the package has
    been installed.

    Args:
        res_name (str): a resource path/name
    """
    # config = mycroft.configuration.Configuration.get()
    # from NGI.utilities.configHelper import NGIConfig as ngiConf
    # config = ngiConf().configuration_available

    # First look for fully qualified file (e.g. a user setting)
    if os.path.isfile(res_name):
        return res_name

    # Now look for ~/.neon/res_name (in user folder)
    filename = os.path.expanduser("~/.neon/" + res_name)
    if os.path.isfile(filename):
        return filename

    # Next look for $dataDir/res/res_name
    data_dir = NGIConfig("ngi_local_conf").content['dirVars']['rootDir']
    filename = os.path.expanduser(join(data_dir, res_name))
    if os.path.isfile(filename):
        return filename

    # Finally look for it in the source package
    filename = os.path.join(os.path.dirname(__file__), '..', 'res', res_name)
    filename = os.path.abspath(os.path.normpath(filename))
    if os.path.isfile(filename):
        return filename

    return None  # Resource cannot be resolved


def check_for_signal(signal_name, sec_lifetime=0):
    """See if a named signal exists

    Args:
        signal_name (str): The signal's name.  Must only contain characters
            valid in filenames.
        sec_lifetime (int, optional): How many seconds the signal should
            remain valid.  If 0 or not specified, it is a single-use signal.
            If -1, it never expires.

    Returns:
        bool: True if the signal is defined, False otherwise
    """
    path = os.path.join('/tmp/neon/ipc', "signal", signal_name)
    if os.path.isfile(path):
        # noinspection PyTypeChecker
        if sec_lifetime == 0:
            # consume this single-use signal
            try:
                os.remove(path)
            except Exception as x:
                print(' >>> ERROR removing signal ' + signal_name + ', error == ' + str(x))
            return True
        if sec_lifetime == -1:
            return True
        try:
            if int(os.path.getctime(path) + sec_lifetime) < int(time.time()):
                # remove once expired
                os.remove(path)
                return False
        except FileNotFoundError:
            # Signal removed while checking
            return False
        return True

    # No such signal exists
    return False


def create_signal(signal_name):
    """Create a named signal. i.e. "CORE_signalName" or "nick_SKILL_signalName
    Args:
        signal_name (str): The signal's name.  Must only contain characters
            valid in filenames.
    """
    try:
        path = os.path.join('/tmp/neon/ipc', "signal", signal_name)
        create_file(path)
        return os.path.isfile(path)
    except IOError:
        return False


def create_file(filename):
    """ Create the file filename and create any directories needed

        Args:
            filename: Path to the file to be created
    """
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError:
        pass
    with open(filename, 'w') as f:
        f.write('')


def delete_recursive_dictionary_keys(dct_to_change, list_of_keys_to_remove):
    # print(type(list_of_keys_to_remove))
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(list_of_keys_to_remove, list):
        raise AttributeError("delete_recursive_dictionary_keys expects a dict and a list as args")

    for key in list_of_keys_to_remove:
        with suppress(KeyError):
            del dct_to_change[key]
    for value in list(dct_to_change.values()):
        if isinstance(value, MutableMapping):
            delete_recursive_dictionary_keys(value, list_of_keys_to_remove)
    return dct_to_change


def dict_merge(dct_to_change, merge_dct):
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(merge_dct, MutableMapping):
        raise AttributeError("merge_recursive_dicts expects two dict objects as args")
    for key, value in merge_dct.items():
        if isinstance(dct_to_change.get(key), dict) and isinstance(value, MutableMapping):
            dct_to_change[key] = dict_merge(dct_to_change[key], value)
        else:
            dct_to_change[key] = value
    return dct_to_change


def dict_make_equal_keys(dct_to_change, keys_dct):
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(keys_dct, MutableMapping):
        raise AttributeError("merge_recursive_dicts expects two dict objects as args")
    for key in list(dct_to_change.keys()):
        # if isinstance(keys_dct.get(key), dict) and isinstance(value, MutableMapping):
        #     dct_to_change[key] = dict_make_equal_keys(value, keys_dct[key])
        # else:
        if key not in keys_dct.keys():
            del dct_to_change[key]
    for key, value in keys_dct.items():
        if key not in dct_to_change.keys():
            dct_to_change[key] = value
    return dct_to_change


def dict_update_keys(dct_to_change, keys_dct):
    if not isinstance(dct_to_change, MutableMapping) or not isinstance(keys_dct, MutableMapping):
        raise AttributeError("merge_recursive_dicts expects two dict objects as args")
    for key, value in list(keys_dct.items()):
        if isinstance(keys_dct.get(key), dict) and isinstance(value, MutableMapping):
            # print("3>>>Recurse")
            dct_to_change[key] = dict_update_keys(dct_to_change.get(key, {}), keys_dct[key])
            # print(f"4>>>{dct_to_change[key]}")
        else:
            if key not in dct_to_change.keys():
                # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                # print(f"{key} = {repr(value)}")
                dct_to_change[key] = repr(value)
    return dct_to_change


class NGIConfig:
    configuration_list = []

    def __init__(self, name, path=None):
        self.name = name
        self.path = path
        self.parser = YAML()
        self.logfile = "/tmp/neon/config.log"
        # self.log("Configuration Init")
        self.lock = FileLock(f"{self.file_path}.lock", timeout=10)
        self.content = self._load_yaml_file()
        if not self.content:
            self.content = {}

        NGIConfig.configuration_list.append(self.name)

    def populate(self, content, check_existing=False):
        # with self.lock.acquire(30):
        if not check_existing:
            self.__add__(content)
            return
        # print(self.content)
        self.content = dict_merge(content, self.content)  # to_change, one_with_all_keys
        self._reload_yaml_file()

    def remove_key(self, *key):
        for item in key:
            self.__sub__(item)

    def make_equal_by_keys(self, other):
        # with self.lock.acquire(30):
        old_content = deepcopy(self.content)
        self.content = dict_make_equal_keys(self.content, other)
        if self.content != old_content:
            self._reload_yaml_file()

    def update_keys(self, other):
        # with self.lock.acquire(30):
        self.content = dict_update_keys(self.content, other)  # to_change, one_with_all_keys
        self._reload_yaml_file()

    def log(self, log_string):
        with open(self.logfile, 'a+') as log:
            print(log_string, file=log)

    @property
    def file_path(self):
        if self.path:
            file_path = join(self.path, self.name + ".yml")
        else:
            file_path = join(dirname(dirname(__file__)), self.name + ".yml")
        if not isfile(file_path):
            create_file(file_path)
            self.log(f"New YAML created: {file_path}")
        return file_path

    @file_path.setter
    def file_path(self, name):
        if isinstance(name, str):
            self.name = name
        else:
            self.log("New value has to be a string")

    def check_for_updates(self):
        new_content = self._load_yaml_file()
        # self.log(new_content)
        if new_content:
            self.log(f"{self.name} Checked for Updates")
            self.content = new_content
        else:
            self.log("ERROR: new_content is empty!!")
            new_content = self._load_yaml_file()
            if new_content:
                self.log("second attempt success")
                self.content = new_content
            else:
                self.log("ERROR: second attempt failed")
        # self.content = self._load_yaml_file()
        return self.content

    # def update_yaml_file(self, yaml_type="user", header=None, sub_header=None, value=None,multiple=False,final=False):
    #     self._update_yaml_file(header=header, sub_header=sub_header, value=value, multiple=multiple, final=final)
    #     if yaml_type:
    #         print("Usage of yaml_type {} is depreciated.".format(yaml_type))

    def update_yaml_file(self, header=None, sub_header=None, value="", multiple=False, final=False):
        """
        Called by class's children to update, create, or initiate a new parameter in the
        specified YAML file. Creates and updates headers, adds or overwrites preference elements,
        associates value to the created or existing field. Recursive if creating a new
        header-preference-value combo.
        :param multiple: true if more than one continuous write is coming
        :param header: string with the new or existing main header
        :param sub_header: new or existing subheader (sublist)
        :param value: any value that should be associated with the headers.
        :param final: true if this is the last change when skip_reload was true
        :return: pre-existing parameter if nothing to update or error if invalid yaml_type.
        """
        # with self.lock.acquire(30):
        before_change = self.content
        # print(before_change[header][sub_header])
        self.log(value)
        # print(before_change[header])
        if header and sub_header:
            try:
                before_change[header][sub_header] = value
            except KeyError:
                before_change[header] = {sub_header: value}
                return
        elif header and not sub_header:
            try:
                before_change[header] = value
            except Exception as x:
                self.log(x)
        else:
            self.log("No change needed")
            if not final:
                return

        if not multiple:
            # self.check_for_updates()
            self._reload_yaml_file()
        else:
            self.log("More than one change")
        # return True

    def _load_yaml_file(self) -> dict:
        """
        Loads and parses the YAML file at a given filepath into the Python
        dictionary object.
        :return: dictionary, containing all keys and values from the most current
                 selected YAML.
        """
        try:
            # self.log("Request load")
            # with self.lock.acquire(30):
            #     self.log("Load lock acquired")
            with open(self.file_path, 'r') as f:
                return self.parser.load(f)
        # except Timeout as t:
        #     self.log(f"Configuration load timeout error: {t}")
        except FileNotFoundError as x:
            self.log(f"Configuration file not found error: {x}")
        except Exception as c:
            self.log(f"Configuration file error: {c}")
        return dict()

    def _reload_yaml_file(self):
        """
        Overwrites and/or updates the YML at the specified file_path.
        :return: updated dictionary of YAML keys and values.
        """
        try:
            with self.lock.acquire(30):
                if self.path:
                    tmp_filename = join(self.path, self.name + ".tmp")
                else:
                    tmp_filename = join(dirname(dirname(__file__)), self.name + ".tmp")
                self.log(f"tmp_filename={tmp_filename}")
                shutil.copy2(self.file_path, tmp_filename)
                with open(self.file_path, 'w+') as f:
                    self.parser.dump(self.content, f)
                    self.log(f"YAML updated {self.name}")
                    os.remove(tmp_filename)
                    # if not multiple:
                    #     return self.load_yaml_file()
                    # return
        except FileNotFoundError as x:
            self.log(f"Configuration file not found error: {x}")

    def __repr__(self):
        return "NGIConfig('{}') \n {}".format(self.name, self.file_path)

    def __str__(self):
        return "{}: {}".format(self.file_path, json.dumps(self.content, indent=4))

    def __add__(self, other):
        # with self.lock.acquire(30):
        if other:
            if not isinstance(other, NGIConfig) and not isinstance(other, MutableMapping):
                raise AttributeError("__add__ expects dict or config object as argument")
            to_update = other
            if isinstance(other, NGIConfig):
                to_update = other.content
            if self.content:
                self.content.update(to_update)
            else:
                self.content = to_update
        else:
            raise TypeError("__add__ expects an argument other than None")
        self._reload_yaml_file()

    def __sub__(self, *other):
        # with self.lock.acquire(30):
        if other:
            for element in other:
                if isinstance(element, NGIConfig):
                    to_remove = list(element.content.keys())
                elif isinstance(element, MutableMapping):
                    to_remove = list(element.keys())
                elif isinstance(element, list):
                    to_remove = element
                elif isinstance(element, str):
                    to_remove = [element]
                else:
                    raise AttributeError("__add__ expects dict, list, str, or config object as the argument")

                if self.content:
                    self.content = delete_recursive_dictionary_keys(self.content, to_remove)
                else:
                    raise TypeError("{} config is empty".format(self.name))
        else:
            raise TypeError("__sub__ expects an argument other than None")
        self._reload_yaml_file()


if __name__ == '__main__':
    try:
        from sys import argv
        local_conf = NGIConfig("ngi_local_conf")

        # google_cloud = NGIConfig("ngi_user_info").content['stt']['google_cloud']
        # if os.path.isfile(os.path.join(local_conf.content["dirVars"]["docsDir"], "google.json")):
        #     with open(os.path.join(local_conf.content["dirVars"]["docsDir"], "google.json")) as creds:
        #         json_credential = json.load(creds)
        # else:
        #     json_credential = None
        # if json_credential and google_cloud.get("credential") != json_credential:
        #     print(">>>>>>>>Invalid Credential found!<<<<<<<<")
        #     google_cloud["credential"] = json_credential
        #     print(google_cloud)
        #     local_conf.content["stt"]["google_cloud"] = google_cloud
        #     # local_conf.update_yaml_file("stt", "google_cloud", google_cloud, final=True)

        if len(argv) > 1:
            local_conf.update_yaml_file("devVars", "version", argv[1])

        local_conf.update_keys(NGIConfig(
            "clean_local_conf", join(dirname(dirname(__file__)), 'utilities')).content)
        NGIConfig("ngi_auth_vars").update_keys(NGIConfig(
            "clean_auth_vars", join(dirname(dirname(__file__)), 'utilities')).content)
        NGIConfig("ngi_user_info").update_keys(NGIConfig(
            "clean_user_info", join(dirname(dirname(__file__)), 'utilities')).content)

        # print(google_cloud)
        user_config = NGIConfig("ngi_user_info")
        if user_config.content["stt"]["google_cloud"].get("credential") and \
                "  " in user_config.content["stt"]["google_cloud"]["credential"]["private_key"]:
            print("Config error! updating!")
            google_cloud = user_config.content["stt"]["google_cloud"]
            google_cloud["credential"]["private_key"] = google_cloud["credential"]["private_key"].replace("  ", "")
            user_config.update_yaml_file("stt", "google_cloud", google_cloud, final=True)

        # Handle added params that need to be initialized (No, this is done in functions.sh
        # if local_conf.content["remoteVars"].get("guiGit") in ("${guiGit}", "''", None):
        #     print("Adding gui git info!!")
        #     local_conf.update_yaml_file("remoteVars", "guiGit", "https://github.com/neongeckocom/neon-gui.git", True)
        #     local_conf.update_yaml_file("remoteVars", "guiBranch", "master", True, True)
        # NGIConfig("ngi_user_info").update_yaml_file("stt", "google_cloud", google_cloud)
        # NGIConfig("ngi_local_conf").update_yaml_file('config', 'devVars', 'version', argv[1])
    except Exception as e:
        print(e)
        print("YML ERRORS")
