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

# import glob
import os
import logging
import pickle
import shutil
import subprocess
import time
import git
import github

from os.path import isfile
from pprint import pformat
from threading import Thread  # , Lock
from typing import Optional
from pydub import AudioSegment
from socketIO_client import SocketIO

from NGI.server.email_utils import write_out_email_attachments, send_ai_email
from NGI.utilities.configHelper import NGIConfig
# from NGI.utilities.lookupUtils import *
# from NGI.utilities.utilHelper import return_close_values as search_string
from NGI.utilities.chat_user_util import get_chat_nickname_from_filename, get_response_filename
from mycroft import Message
# from mycroft.device import get_ip_address
from neon_utils.net_utils import get_ip_address
from neon_utils.location_utils import *
from neon_utils.search_utils import search_convo_dict
from mycroft.messagebus import MessageBusClient
from mycroft.util import LOG, reset_sigint_handler, create_daemon, wait_for_exit_signal, check_for_signal, deepcopy
from mycroft.lock import Lock as PIDLock

# Connections
css = SocketIO('https://localhost', 8888, verify=False)
bus: Optional[MessageBusClient] = None  # Mycroft messagebus connection
# lock = Lock()

# Klat conversation cache
DOM_LIST = list()
DOM_DICT = dict()
CON_DICT = dict()
MSG_DICT = dict()
MAX_AGE = int(round(time.time() * 1000)) - (180 * 86400000)  # Throw out older shouts and conversations (180 Days)
# LOG.debug(f"Oldest conversation: {MAX_AGE}")

# SKILLS_PENDING = list()

# Location lookup cache
LOCAL_CONFIG = NGIConfig("ngi_local_conf").content
loc_cache = LOCAL_CONFIG["dirVars"]["cacheDir"] + "/location"
LOC_DICT = dict()

# def get_most_recent(path):
#     list_of_files = glob.glob(path)  # * means all if need specific format then *.csv
#     if list_of_files:
#         latest_file = max(list_of_files, key=os.path.getctime)
#         return latest_file
#     else:
#         return None


def run_listener():
    css.wait()


# SocketIO Handlers
def on_connect():
    """
    SocketIO handler for connection to server established
    """
    LOG.debug("SocketIO Connected")
    # Populate internal conversation cache
    css.emit("get crosspost words")
    css.emit("get all conversations")
    css.emit("get all shouts")


def on_disconnect():
    """
    SocketIO handler for disconnection from server
    """
    LOG.error("Chat Server Socket Disconnected!")


def on_reconnect():
    """
    SocketIO handler for reconnection to server
    """
    LOG.debug("SocketIO Reconnected")


def on_crosspost_words(*args):
    """
    SocketIO handler for 'crosspost words'
    Gets keywords for each domain and populates internal cache
    """
    raw_dict = dict(args[0])
    for dom in raw_dict.keys():
        words = [dom.lower(), raw_dict[dom]["sitename"].lower()]
        words += (raw_dict[dom]["sitename"].lower().split(" "))
        if raw_dict[dom]["crossPostWords"]:
            words += (raw_dict[dom]["crossPostWords"].lower().split(", "))
        words = [word for word in words if word and word != ""]
        DOM_DICT[dom] = words
        DOM_LIST.append(dom)
        # LOG.info(raw_dict.get(dom))
        # LOG.info(DOM_DICT.get(dom))
    LOG.debug(len(DOM_DICT))


def on_conversation_list(*args):
    """
    SocketIO handler for 'conversations'
    Gets a list of all conversations and populates internal cache
    """
    raw_dict = dict(args[0])
    for c in raw_dict.keys():
        try:
            if raw_dict[c]["dom"] != "Private" and int(raw_dict[c]["updated"]) > MAX_AGE:
                cid = c
                title = raw_dict[cid]["title"]
                domain = raw_dict[cid]["dom"]
                clean_title = str(title).lower().rsplit('-', 1)[0].replace(u'\u201d', '').replace(u'\u201c', '')\
                    .replace('"', "").replace("'", "").replace("&apos;", "")
                words = clean_title.split(' ')
                words = [word for word in words if word and word != ""]
                CON_DICT[f"{domain},{cid},{clean_title}"] = words
        except Exception as x:
            LOG.error(x)
        # LOG.info(raw_dict[cid])
        # LOG.info(CON_DICT[f"{domain},{cid},{clean_title}"])
    LOG.debug(len(CON_DICT))


def on_shout_list(*args):
    """
    SocketIO handler for 'shouts'
    Gets a list of all shouts and populates internal cache
    """
    raw_dict = dict(args[0])
    for s in raw_dict.keys():
        shout = raw_dict[s]
        if shout['dom'] != "Private" and int(raw_dict[s]["created"]) > MAX_AGE:
            dom = shout['dom']
            cid = shout['cid']
            millis = shout['created']
            try:
                msg = bytes(str(shout['msg']), "utf-8").decode("utf-8", "ignore")\
                    .replace(u'\u02c8', '').replace(u'\u02d0', '').split("<br />AI Translate:")[0]
            except Exception as x:
                LOG.error(x)
                msg = shout['msg']
            user = shout['nick']
            sid = shout['shout_id']
            # LOG.info(f"{cid},{millis},{user},{msg}")
            MSG_DICT[f"{dom},{cid},{millis},{user},{sid},{msg}"] = str(msg).lower().split(' ')
            # LOG.info(raw_dict[s])
            # LOG.info(MSG_DICT[f"{dom},{cid},{millis},{user},{sid},{msg}"])
    LOG.info(len(MSG_DICT))


def on_create_conversation_return(*args):
    """
    SocketIO handler for 'create conversation return'
    Called if Neon tries to send a private message to a user. Server created or found the appropriate private
    conversation and emitted this message so Neon can send the message to that conversation.
    """
    LOG.debug(args[5])
    data = args[5]
    lang = data.get("lang")
    if str(args[0]).startswith("Title exists"):
        cid = str(args[0]).split(" - ")[1]
    else:
        cid = str(args[0])

    try:
        LOG.debug("Emitting private message")
        handle_css_emit(Message("css.emit", {"event": "mycroft response",
                                             "data": [data.get("sentence"), data.get("filename"), lang, cid]}))
    except Exception as x:
        LOG.error(x)


# Messagebus handlers
def handle_css_emit(message):
    """
    Messagebus handler for "css.emit"
    Accepts message.data params 'event' (str) and 'data' (list); translates those to a structure for css.emit
    """
    LOG.debug(f"going to emit: {message.data}")
    event = message.data.get("event")
    data = message.data.get("data", [])
    if not event:
        raise ValueError("No event name specified")
    css.emit(event, *data)
    # if len(data) == 1:
    #     css.emit(event, data[0])
    # elif len(data) == 2:
    #     css.emit(event, data[0], data[1])
    # elif len(data) == 3:
    #     css.emit(event, data[0], data[1], data[2])
    # elif len(data) == 4:
    #     css.emit(event, data[0], data[1], data[2], data[3])
    # elif len(data) == 5:
    #     css.emit(event, data[0], data[1], data[2], data[3], data[4])
    # elif len(data) == 6:
    #     css.emit(event, data[0], data[1], data[2], data[3], data[4], data[5])
    # elif len(data) == 7:
    #     css.emit(event, data[0], data[1], data[2], data[3], data[4], data[5], data[6])
    # elif len(data) == 8:
    #     css.emit(event, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7])
    # else:
    #     LOG.error("!!! more arguments than expected !!!")

    if event == "mycroft response":
        message.context.get("timing", {})["processed"] = time.time()
        # TODO: Handle some reply confirmation? DM
        # This is here for checking duration in logs
        LOG.debug(f"TIME: sent to chat server, {time.time()}, {message.context}")


def handle_get_location(message):
    """
    Messagebus handler for "get_location"
    Expects message.data to contain either ('lat', 'lng') or ('city', 'state', 'country'); builds a complete location
    dict and emits back to the server via SocketIO
    """
    nick = message.data.pop("nick")
    lat = message.data.get("lat")
    lng = message.data.get("lng")
    city = message.data.get("city")
    state = message.data.get("state")
    country = message.data.get("country")
    # Latitude and Longitude provided
    if lat and lng:
        cache_key = f"{lat},{lng}"
    elif city and state and country:
        cache_key = f"{city},{state},{country}"
    else:
        LOG.error("Cannot get location without lat/lng or city/state/country")
        return
    if cache_key in LOC_DICT:
        location_to_return = deepcopy(LOC_DICT[cache_key])
    else:
        location_to_return = dict()
        if lat and lng:
            location_to_return["lat"] = lat
            location_to_return["lng"] = lng
            city, county, state, country = get_location(lat, lng)
            location_to_return["city"] = state
            location_to_return["county"] = county
            location_to_return["state"] = state
            location_to_return["country"] = country
        else:
            lat, lng = get_coordinates({"city": city,
                                        "state": state,
                                        "country": country})
            location_to_return["city"] = city
            location_to_return["state"] = state
            location_to_return["country"] = country
            location_to_return["lat"] = lat
            location_to_return["lng"] = lng
        LOC_DICT[cache_key] = location_to_return
        with open(loc_cache, 'wb+') as cached_locations:
            pickle.dump(LOC_DICT, cached_locations)

    location_to_return["nick"] = nick

    tz, _ = get_timezone(message.data["lat"], message.data["lng"])
    location_to_return['timezone'] = tz
    LOG.debug(location_to_return)

    if location_to_return and len(location_to_return) > 0:
        # TODO: Makes more sense to reply via Messagebus; requires change to Klat Server DM
        css.emit('location update', message.data)
    else:
        LOG.warning("Skipping emit of incomplete location dict")


# def handle_cache_update(message):
#     cache = message.data['cache']
#     dict_to_cache = message.data["dict"]
#
#     if cache == "location_cache":
#         LOG.debug(f"DM: location cache update: {dict_to_cache}")
#         with open(loc_cache, 'rb+') as cached_locations:
#             pickle.dump(dict_to_cache, cached_locations)
#     elif cache == "coord_cache":
#         LOG.debug(f"DM: coordinate cache update: {dict_to_cache}")
#         with open(coord_cache, 'rb+') as cached_locations:
#             pickle.dump(dict_to_cache, cached_locations)


def handle_script_upload(message):
    """
    Messagebus handler for a conversation script uploaded via klat.com.
    The plaintext script as well as compiled version are handled here.
    :param message: message associated with upload event
    """
    file_text = message.data.get("nctText")
    flac_file = message.data.get("filename")
    output_path = os.path.join(LOCAL_CONFIG["dirVars"]["skillsDir"], "custom-conversation.neon", "script_txt")
    repo = git.Repo(output_path)
    repo.remote("origin").pull()
    from script_parser import ScriptParser
    parser = ScriptParser()

    try:
        script_dict = parser.parse_text_to_dict(file_text)
        script_name = script_dict["meta"]["title"]
        script_author = script_dict["meta"]["author"]
        script_uploader = get_chat_nickname_from_filename(flac_file)
        if not script_name:
            LOG.warning(f"{script_name} is invalid because there is no valid title!")
            bus.emit(Message("neon.script_upload", {"script_name": script_name,
                                                    "script_author": script_author,
                                                    "script_status": "no title"}, {"flac_filename": flac_file}))
            return
        file_basename = script_name.strip('"').strip("'").replace(' ', '_').lower()
        file_name = f"{file_basename}.{parser.file_ext}"
        output_file = os.path.join(output_path, file_name)
    except Exception as e:
        LOG.error(e)
        return

    file_exists = False
    try:
        if os.path.isfile(output_file):
            file_exists = True
            old_script = parser.parse_script_to_dict(output_file)
            # old_name = old_script.get("meta", {}).get("title")  # Old scripts have no meta
            LOG.debug(old_script.get("meta"))
            if not old_script.get("meta", {}).get("uploader") or \
                    old_script.get("meta", {}).get("uploader") == script_uploader:
                backup_file = os.path.join(output_path, "backup",
                                           f"{file_basename}_{time.strftime('%Y-%m-%d--%H_%M')}")
                shutil.move(output_file, backup_file)
    except Exception as e:
        LOG.error(e)
        os.remove(output_file)

    try:
        if os.path.isfile(output_file):
            # We can't overwrite someone else's script
            LOG.debug("Upload Declined.")
            bus.emit(Message("neon.script_upload", {"script_name": script_name,
                                                    "script_author": script_author,
                                                    "script_status": "exists"}, {"flac_filename": flac_file}))
        else:
            try:
                parser.parse_text_to_file(file_text, output_file, meta={"uploader": script_uploader})
                LOG.debug(f"wrote out {output_file}")
            except Exception as e:
                LOG.error(e)

            # Write out text (nct) file
            # filename = script_name.replace(' ', '_') + ".nct"
            file_basename = script_name.strip('"').strip("'").replace(' ', '_').lower()
            file_to_write = os.path.join(output_path, f"{file_basename}.nct")

            if os.path.isfile(file_to_write):
                LOG.warning(f"{file_to_write} exists and will be overwritten!")
            with open(file_to_write, "w") as file:
                file.write(file_text)
            LOG.debug(f"wrote out {script_name}")
            LOG.debug(f"{script_name}|{script_author}|{flac_file}")
            if file_exists:
                bus.emit(Message("neon.script_upload", {"script_name": script_name,
                                                        "script_author": script_author,
                                                        "script_status": "updated",
                                                        "file_basename": file_basename}, {"flac_filename": flac_file}))

            else:
                bus.emit(Message("neon.script_upload", {"script_name": script_name,
                                                        "script_author": script_author,
                                                        "script_status": "created",
                                                        "file_basename": file_basename}, {"flac_filename": flac_file}))
            LOG.debug("DM: About to git add/commit")
            repo.git.add(output_file)
            repo.git.add(file_to_write)
            repo.index.commit(f"{file_basename} Uploaded via Klat")
            LOG.debug("DM: About to push")
            repo.git.push()
    except Exception as e:
        LOG.error(e)


def handle_mobile_request(message):
    """
    Messagebus entry point for Klat-connected mobile requests to Neon core/skills
    :param message: Message object derived from mobile emit
    """
    # TODO: Most of these should be supported for direct messagebus connections too; consider making this an adapter DM
    LOG.debug(f"DM: {message}")
    kind = message.data.get("name")
    data = message.data.get("data")
    LOG.debug(f"{kind} | {data}")
    if kind == "domain search term":
        # Accepts a search term and generates a list of results
        LOG.debug(data)
        sender = data[0]
        search = data[1]
        LOG.debug(f"{sender} wants a domain about {search} in {len(DOM_DICT)} domains")
        results = search_convo_dict(DOM_DICT, search, 8)
        LOG.debug(results)
        # css.emit("mobile request from neon", "domain search results", results, sender)
        css.emit("mobile request from neon", "search results", results, sender)
    elif kind == "conversation search term":
        LOG.debug(data)
        sender = data[0]
        search = data[1]
        LOG.debug(f"{sender} wants a conversation about {search} in {len(CON_DICT)} conversations")
        temp_results = search_convo_dict(CON_DICT, search, 8, False)
        LOG.debug(temp_results)
        results = dict()
        for result in temp_results:
            data = str(result).split(',', 2)
            dom = data[0]
            cid = data[1]
            title = data[2]
            results[title] = {"domain": dom,
                              "cid": cid}
            pass
        css.emit("mobile request from neon", "search results", results, sender)
    elif kind == "shout search term":
        LOG.debug(data)
        sender = data[0]
        search = data[1]
        LOG.debug(f"{sender} wants a shout about {search} in {len(MSG_DICT)} shouts")
        temp_results = search_convo_dict(MSG_DICT, search, 8, False)
        LOG.debug(temp_results)
        results = dict()
        for result in temp_results:
            data = str(result).split(',', 5)
            dom = data[0]
            cid = data[1]
            millis = data[2]
            user = data[3]
            sid = data[4]
            text = data[5]
            results[f"{user}: {text}"] = {"domain": dom,
                                          "cid": cid,
                                          "millis": millis,
                                          "shout": text,
                                          "sid": sid}
        LOG.debug(results)
        css.emit("mobile request from neon", "search results", results, sender)
    elif kind == "get domain list":
        LOG.debug(data)
        css.emit("mobile request from neon", "domain list", DOM_LIST, data)
    elif kind == "get scripts list":
        LOG.debug(f"DM: Get Scripts List! {data}")
        response = bus.wait_for_response(message.forward("neon.get_scripts"))
        available = response.data.get("available_scripts")  # TODO: This needs to be tested
        LOG.debug(f"DM: {available}")
        css.emit("mobile request from neon", "scripts list", available, data)
    elif kind == "send email":
        LOG.debug(data)
        description = data[0]
        email_addr = data[1]
        device_id = data[2]
        LOG.debug(f"send {description} to {email_addr} regarding device: {device_id}")
        title = "Neon AI Mobile Support"
        body = f"Your support request has been received. If you want to provide more information, you may email " \
               f"info@neongecko.com. Please include your Device ID with any emails.\n\n" \
               f"Issue Description: {description}\nDevice ID: {device_id}\n\n-Neon"
        bus.emit(Message("neon.email", {"email": email_addr, "title": title, "body": body}))
    elif kind == "confirm phone number":
        LOG.debug(data)
        contact_data = data[0]
        dev_id = data[1]
        nick = data[2]
        LOG.debug(contact_data)
        bus.emit(Message("neon.messaging.confirmation", {"contact_data": contact_data,
                                                         "sender": nick,
                                                         "dev_id": dev_id}))
    elif kind == "neon speak":
        # TODO: Finish this DM
        LOG.debug(data)
        to_say = data[0]
        sid = data[1]
        sender = data[2]
        LOG.debug(f"speak {to_say} to {sender} at {sid}")
        # bus.emit(Message("speak", {'utterance': to_say,
        #                            'expect_response': False,
        #                            'cc_data': None,
        #                            'private': True,
        #                            'nick': sender}))


def handle_chat_user_response(message):
    """
    Messagebus handler for "recognizer_loop:chatUser_response". Handles responses from Neon and sends them to Klat
    """
    LOG.info(message.data)
    responses = message.data["responses"]
    request_id = message.context["klat_data"]["request_id"]
    LOG.debug(responses)
    if message.data.get("speaker"):
        utt_from = message.data["speaker"].get("name", "Neon")
    else:
        utt_from = "Neon"

    sudo_password = ''

    server_ip = get_ip_address()
    # LOG.debug(f"server IP = {server_ip}")
    for server, password in list(NGIConfig("ngi_auth_vars").content['servers'].items()):
        if server in server_ip:
            sudo_password = password

    for lang in responses.keys():
        # LOG.debug(lang)
        response_data = responses[lang]
        try:
            # LOG.debug(f"data={message.data}")
            if message.data and message.data.get("speaker").get("override_user", False):
                # LOG.debug(lang)
                lang = f"00_{lang}"  # This is handled on the chat server as going to all users, regarless of user lang
        except Exception as e:
            LOG.error(e)

        # LOG.debug(f"{lang} = {response_data}")
        response_audio_files = [response_data.get("male", None), response_data.get("female", None)]

        if response_audio_files[0] is None:
            gender = 'female'
        elif response_audio_files[1] is None:
            gender = 'male'
        else:
            gender = 'both'

        LOG.debug(response_audio_files)
        sentence = response_data.get("sentence")
        LOG.debug(sentence)

        for i in (0, 1):
            if response_audio_files[i]:
                neon_response_audio = response_audio_files[i]
                # LOG.debug(f"Processing: {neon_response_audio}")
                file_ext = os.path.splitext(neon_response_audio)[1]
                path_to_check = f'/var/www/html/klatchat/app/files/chat_audio/{request_id}{file_ext}'
                try:
                    response_filename = get_response_filename(path_to_check)
                    LOG.debug(f"write audio response to: {response_filename}")
                    if os.path.isfile(neon_response_audio):
                        command = f'cp {neon_response_audio} {response_filename}'
                        p = subprocess.call('echo %s|sudo -S %s' % (sudo_password, command), shell=True)
                        command = f'chown root:root {response_filename}'
                        q = subprocess.call('echo %s|sudo -S %s' % (sudo_password, command), shell=True)
                        LOG.debug(f"copy_status={p} | chown_status={q}")
                        new_filename = os.path.basename(response_filename)
                        response_audio_files[i] = new_filename
                    else:
                        LOG.warning(f"{neon_response_audio} doesn't exist!")
                        response_audio_files[i] = None
                except Exception as e:
                    LOG.error(f"error == {e}")
        # LOG.debug(response_audio_files)

        # LOG.debug(f"emitting: {sentence} | lang={lang} | gender={gender}")
        # LOG.debug(f"audio_files: {response_audio_files}")
        bus.emit(Message("css.emit", {"event": "mycroft response",
                                      "data": [sentence, response_audio_files, lang, None, utt_from, gender]}))

        # LOG.debug(f"data|context={message.data}|{message.context}")

        if message.context["cc_data"].get("signal_to_check", ""):
            LOG.info(f'clear signal: {message.context["cc_data"]["signal_to_check"]}')
            check_for_signal(message.context["cc_data"]["signal_to_check"])


def handle_brands_update(message):
    """
    Messagebus handler for "neon.server.update_brands" (client) and "neon.update_brands". Server use only.
    Handles brand and coupon updates from trackmybrands.com database
    :param message: Message associated with request
    """
    from NGI.server.sql_utils import get_info_from_tmb
    try:
        output = get_info_from_tmb()
        LOG.debug("brands written")
        if message.msg_type == "neon.server.update_brands":
            LOG.debug("replying to remote device request")
            with open(os.path.join(output, "NewAudioBrandCoupons.csv"), "r") as f:
                csv = f.read()
            with open(os.path.join(output, "BrandName.voc"), "r") as f:
                brands = f.read()
            data = {"success": True,
                    "csv": csv,
                    "brands": brands}
            LOG.debug(f"response={data}")
            reply = message.response(data=data)
            bus.emit(reply)
    except Exception as e:
        LOG.error(e)
        # Notify client of error
        if message.msg_type == "neon.server.update_brands":
            LOG.debug("replying to remote device request")
            data = {"success": False}
            LOG.debug(f"response={data}")
            reply = message.response(data=data)
            bus.emit(reply)


def handle_send_email(message):
    """
    Messagebus handler for "neon.server.send_email" (client) and "neon.send_email" (server).
    Builds and sends an email from the server-configured address.
    """
    try:
        att_files = write_out_email_attachments(message)
        recipient = message.data.get("email")
        subject = message.data.get("title")
        body = message.data.get("body")
        send_ai_email(subject, body, att_files, recipient)
        for file in att_files:
            os.remove(file)
        # bus.emit(message.forward("neon.email", message.data))
        bus.emit(message.response({"success": True}))
    except Exception as e:
        LOG.error(e)
        bus.emit(message.response({"success": False,
                                   "exception": repr(e)}))


def handle_check_release(message):
    """
    Messagebus handler for "neon.client.check_release". Checks the release version of a hard-coded git repository and
    replies to the incoming request.
    """
    release = "0.0"
    LOG.debug(f"Requesting release check")
    shared_repo = "NeonGeckoCom/neon-shared-core"
    repo_branch = "dev"  # TODO: This should be variable or later default to master
    try:
        gh = github.Github(login_or_token=NGIConfig("ngi_auth_vars").content.get("git", {}).get("token"))
        repo = gh.get_repo(shared_repo)
        branch = repo.get_branch(repo_branch)
        tree = repo.get_git_tree(branch.raw_data.get("commit").get("sha"), recursive=True)
        for e in tree.tree:
            if e.path.endswith(".release"):
                LOG.debug(e.path)
                release = e.path.split("/", 1)[1].rsplit(".", 1)[0]
                LOG.debug(release)
    except Exception as e:
        LOG.error(e)
    major, minor = release.split('.')
    data = {"version_major": major, "version_minor": minor, "repo": shared_repo, "branch": repo_branch}
    bus.emit(message.response(data))


def handle_client_connection(message):
    """
    Messagebus handler for "neon.client.announce_connection"
    Logs a remote device connection to this server in the log
    :param message: message sent from remote device
    """
    LOG.debug(f"Client Connection: {message.data} | {message.context}")
    connection_log = f'{LOCAL_CONFIG["dirVars"]["diagsDir"]}/connections.log'
    data = message.data
    with open(connection_log, "a") as log:
        log.write(f'{data["time"]},{data["ver"]},{data["name"]},{data["host"]}\n')


def handle_metric(message):
    """
    Messagebus handler for "neon.metric"
    Logs a reported metric
    """
    data = message.data
    # TODO: Add utterance timing metric emit/handling
    if data.get("name") == "failed-intent":
        LOG.info("Intent Failure reported!")
        missed_intent_log = f'{LOCAL_CONFIG["dirVars"]["diagsDir"]}/missed_intents.log'
        with open(missed_intent_log, "a") as log:
            log.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")},{data.get("device")},{data.get("utterance")}\n')
    elif data.get("name") == "diagnostics":  # TODO: This should probably have it's own handler DM
        LOG.info("Diagnostics Uploaded!")
        host = data.get("host")
        uploaded = time.strftime("%Y-%m-%d_%H-%M-%S")
        upload_dir = os.path.join(LOCAL_CONFIG["dirVars"]["diagsDir"], "uploaded", f"{uploaded}__{host}")

        try:
            os.makedirs(upload_dir)
            # Write status
            with open(os.path.join(upload_dir, "status.log"), "a") as status_log:
                status_log.write(data.get("status"))
                status_log.write("\n")
            # Write configurations
            for key, val in data.get("configurations").items():
                try:
                    with open(os.path.join(upload_dir, key), "a") as file:
                        file.write(pformat(val))
                        file.write("\n")
                except Exception as e:
                    LOG.error(e)
                    LOG.debug(data.get("configurations"))
            # Write transcripts
            if data.get("transcripts"):
                try:
                    with open(os.path.join(upload_dir, "transcripts.csv"), "a") as transcripts:
                        transcripts.write(data.get("transcripts"))
                        transcripts.write("\n")
                except Exception as e:
                    LOG.error(e)
                    LOG.debug(data.get("transcripts"))
            # Write logs
            if data.get("logs"):
                for key, val in data.get("logs").items():
                    try:
                        with open(os.path.join(upload_dir, f"{key}.log"), "a") as file:
                            file.write(val)
                            file.write("\n")
                    except Exception as x:
                        LOG.error(key)
                        LOG.error(x)
        except Exception as e:
            LOG.error(e)

    else:
        LOG.info("other metric reported")
        metric_log = f'{LOCAL_CONFIG["dirVars"]["diagsDir"]}/metrics.log'
        with open(metric_log, "a") as log:
            log.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")},{data}\n')


def handle_shout(message):
    """
    Messagebus handler for "klat.shout"
    Main entry point for Klat shouts into the Neon core
    """
    # shouts_folder = LOCAL_CONFIG["dirVars"]["docsDir"]
    audio_file = message.data.get("audio_file")
    nano = message.data.get("nano")
    nick = message.data.get("nick")
    cid_nicks = message.data.get("nicks", nick).split(',')
    text = message.data.get("text")
    sid = message.data.get("sid")
    cid = message.data.get("cid")
    title = message.data.get("title")
    encrypted_sid = message.data.get("socketIdEncrypted")

    need_transcription = text == "Spoken:"

    if audio_file and os.path.exists(audio_file):
        LOG.debug(audio_file)
        # LOG.debug(os.path.isfile(audio_file))
        song = AudioSegment.from_file(audio_file)
        if need_transcription:
            # LOG.info(song.dBFS)
            # LOG.info(song.duration_seconds)
            # TODO: Read params from config DM
            minimum_level = -25.0
            minimum_length = 2.0
            if song.dBFS < minimum_level or song.duration_seconds < minimum_length:
                LOG.info('audio too quiet or too short.')
                handle_css_emit(Message("recognizer_loop.server_response",
                                        {"event": "audio too quiet from mycroft",
                                         "data": [audio_file]}, {}))
                os.remove(audio_file)
                return
            else:
                LOG.info('audio loud or long enough to use.')
    else:
        audio_file = None
    # LOG.debug(f"Handling utterance with audio: {audio_file}")
    msg = Message("recognizer_loop:klat_utterance", {"raw_audio": audio_file,
                                                     "shout_text": text, "need_transcription": need_transcription,
                                                     "cid_nicks": cid_nicks, "nano": nano, "user": nick,
                                                     "cid": cid, "sid": sid, "title": title,
                                                     "socketIdEncrypted": encrypted_sid})
    bus.emit(msg)


def main():
    global bus
    global LOC_DICT
    reset_sigint_handler()
    PIDLock("server")
    bus = MessageBusClient()

    # Neon Core Originated
    bus.on('neon.update_brands', handle_brands_update)
    bus.on('neon.server.update_brands', handle_brands_update)
    bus.on('neon.server.send_email', handle_send_email)
    bus.on('neon.send_email', handle_send_email)
    bus.on("neon.client.check_release", handle_check_release)
    bus.on("neon.client.announce_connection", handle_client_connection)
    bus.on('get_location', handle_get_location)
    bus.on("css.emit", handle_css_emit)
    # bus.on('neon.update_cache', handle_cache_update)
    bus.on('nct_file_update', handle_script_upload)
    bus.on("neon.mobile_request", handle_mobile_request)
    bus.on("neon.metric", handle_metric)
    bus.on("recognizer_loop:chatUser_response", handle_chat_user_response)

    # Klat Server Originated
    bus.on("klat.shout", handle_shout)

    logging.getLogger("socketIO-client").setLevel(logging.WARNING)
    logging.getLogger("github.Requester").setLevel(logging.WARNING)
    logging.getLogger("pydub.converter").setLevel(logging.WARNING)
    logging.basicConfig()
    css.on("connect", on_connect)
    css.on("disconnect", on_disconnect)
    css.on("reconnect", on_reconnect)
    css.on("crosspost words", on_crosspost_words)
    css.on("conversations", on_conversation_list)
    css.on("shouts", on_shout_list)
    css.on("create conversation return", on_create_conversation_return)
    event_thread = Thread(target=run_listener)
    event_thread.setDaemon(True)
    event_thread.start()
    LOG.debug(css.get_namespace())

    start_time = time.time()
    if isfile(loc_cache):
        LOG.debug("DM: cache exists")
        with open(loc_cache, 'rb') as cached_locations:
            try:
                locations = pickle.load(cached_locations)
                LOC_DICT = dict(locations)
                # for location in locations:
                #     LOC_DICT[location] = locations[location]
            except Exception as x:
                LOG.error(x)
    LOG.debug(f"cached location load time={time.time() - start_time}")
    create_daemon(bus.run_forever)

    wait_for_exit_signal()


if __name__ == "__main__":
    main()
