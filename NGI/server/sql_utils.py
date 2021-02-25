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

import csv
import os
import shutil
import mysql.connector
from re import sub
from mysql.connector import Error
from mycroft.util.log import LOG
from NGI.utilities.configHelper import NGIConfig, create_signal, check_for_signal


def get_scripts_from_ngi():
    """
    Depreciated function to read scripts from a SQL database
    :return:
    """
    from script_parser import ScriptParser
    LOG.debug("Updating scripts!")
    script_parser = ScriptParser()
    path = '/home/neongecko/conversations'  # Temp path to write-out files
    auth = NGIConfig("ngi_auth_vars").content
    config = NGIConfig("ngi_local_conf").content
    host = auth['neon_gecko_net']['host']
    user = auth['neon_gecko_net']['user']
    password = auth['neon_gecko_net']['password']
    database = auth['neon_gecko_net']['database']
    skill_dir = os.path.join(config["dirVars"]["skillsDir"], "custom-conversation.neon")
    klat_uploads = NGIConfig("CustomConversations", skill_dir).content["updates"]
    LOG.debug(f"NGI Connect: {host} {database}")
    connection = None
    cursor = None

    try:
        # Backup Old Conversations
        if os.path.exists(f"{path}_bak"):
            if os.path.exists(f"{path}_bak2"):
                os.rmdir(f"{path}_bak2")
            shutil.move(f"{path}_bak", f"{path}_bak2")
        shutil.move(path, f"{path}_bak")
    except Exception as e:
        LOG.error(e)
    try:
        connection = mysql.connector.connect(host=host, database=database,
                                             user=user, password=password)
        if connection.is_connected():

            # Clear download location (temp path)
            os.system("rm -rf " + path)
            LOG.debug(path)
            os.makedirs(path, exist_ok=True)

            # LOG.debug("Connected to MySQL database... MySQL Server version on " + db_Info)
            cursor = connection.cursor()
            content = None
            cursor.execute("select sid, name, value from drup_webform_submission_data \
                            where webform_id = 'script' and name in ('script_content', 'script_title_')")

            rows = cursor.fetchall()
            for row in rows:
                try:
                    if row[1] == 'script_content':
                        content = sub(u'\u2018', "'",
                                      sub(u'\u2019', "'",
                                          sub(u'\u201c', '"',
                                              sub(u'\u201d', '"', str(row[2]))).replace('\r\n', '\n')))
                        output = script_parser.parse_text_to_file(content, path)  # Generate .ncs in place
                        LOG.debug(f"wrote: {output}")
                    if row[1] == 'script_title_':
                        LOG.debug(row[2])
                        with open(os.path.join(path, str(row[2]).lower().strip().replace(' ', '_') + '.nct'), 'w') \
                                as output:
                            output.write(content)  # Generate .nct
                            LOG.debug(f"wrote: {output}")
                except Exception as e:
                    LOG.error(e)
            LOG.debug("Scripts Updates Complete!")
        else:
            LOG.error(">>>!!! Connection Failed !!!<<<")
    except Error as e:
        LOG.debug("Error while connecting to MySQL" + str(e))
        shutil.rmtree(path, ignore_errors=True)
        shutil.move(f"{path}_bak", path)
    except Exception as f:
        LOG.error(f)
        shutil.rmtree(path, ignore_errors=True)
        shutil.move(f"{path}_bak", path)
    finally:
        shutil.rmtree(f"{path}_bak")
        # closing database connection.
        if connection and connection.is_connected():
            cursor.close()
        # Copy to skills directory
        # LOG.debug("About to move scripts")
        # os.system(f"rm -f {script_path}/*")  This would remove any scripts that don't exist on the remote
        # os.system(f"cp -rf {path}/* {script_path}")  # This will overwrite Klat uploads DM
        LOG.debug("Scripts written!")

        for script in klat_uploads.keys():
            LOG.info(f"Overwriting .net with klat upload: {script}")
            ncs = os.path.join(skill_dir, "script_txt", f"{script}.{script_parser.file_ext}")
            nct = os.path.join(skill_dir, "script_txt", f"{script}.nct")
            # if os.path.exists(ncs):
            #     shutil.copy(ncs, os.path.join(path, f"{script}.{script_parser.file_ext}"))
            if os.path.exists(nct):
                shutil.copy(nct, os.path.join(path, f"{script}.nct"))
                script_parser.parse_script_to_file(nct, path)
            elif os.path.exists(ncs):
                # TODO: Load this and re-parse the text if parser is updated DM
                LOG.warning(f"No nct file available for {script}!")

        # create_signal("CC_convoSuccess")
        # check_for_signal("CC_updating")
        return path


def get_info_from_tmb():
    import mysql.connector
    from mysql.connector import Error

    cursor = None
    connection = None
    config = NGIConfig("ngi_auth_vars").content
    local_config = NGIConfig("ngi_local_conf").content
    host = config['track_my_brands']['host']
    user = config['track_my_brands']['user']
    password = config['track_my_brands']['password']
    database = config['track_my_brands']['database']
    LOG.debug(f"TMB Connect: {host} {database}")
    skills_loc = local_config["dirVars"]["skillsDir"] + "/i-like-coupons.neon/"
    i_like_loc = local_config["dirVars"]["skillsDir"] + "/i-like-brands.neon/vocab/en-us/"
    brandscoupons_loc = '/home/neongecko/brandscoupons/'

    try:
        connection = mysql.connector.connect(host=host, database=database,
                                             user=user, password=password,
                                             connection_timeout=10)
        if connection and connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("select sid, property, delta, value from drup_webform_submission_data \
                            where webform_id = 'brand_registration' \
                            and property in ('brandname','coupondescription','couponcode') \
                            group by sid, delta, property, value;")
            os.makedirs(skills_loc, exist_ok=True)
            with open(skills_loc + 'TmpAudioBrandCoupons.csv', 'w', newline='') as newCouponCSV:
                writer = csv.writer(newCouponCSV, quoting=csv.QUOTE_ALL)
                brands_file = open(skills_loc + "brandNames0911.txt", 'r+')
                existing_brands = brands_file.read().splitlines()
                with open(skills_loc + "brandNames0911.txt", 'a') as brands_file:
                    brandname = ''
                    coupon_value = ''
                    coupon_code = ''
                    rows = cursor.fetchall()
                    index_save = str(rows[0][0]) + str(rows[0][2])
                    for row in rows:
                        # create a new 'NewAudioBrandCoupons.csv'
                        if index_save == str(row[0]) + str(row[2]):
                            if row[1] == 'brandname':
                                brandname = row[3]
                            if row[1] == 'coupondescription':
                                coupon_value = row[3]
                            if row[1] == 'couponcode':
                                coupon_code = row[3]
                        else:
                            writer.writerow([brandname.lower(), coupon_value, coupon_code])
                            index_save = str(row[0]) + str(row[2])
                            if row[1] == 'brandname':
                                brandname = row[3]
                            if row[1] == 'coupondescription':
                                coupon_value = row[3]
                            if row[1] == 'couponcode':
                                coupon_code = row[3]

                            if brandname.lower() not in existing_brands:
                                brands_file.write(brandname.lower())
                                brands_file.write('\n')
                                existing_brands.append(brandname.lower())

                    brandname = rows[cursor.rowcount - 3][3]
                    coupon_code = rows[cursor.rowcount - 2][3]
                    coupon_value = rows[cursor.rowcount - 1][3]

                    writer.writerow([brandname.lower(), coupon_value, coupon_code])
                    LOG.debug("Brands update complete!")
                    # return skills_loc
    except Error as e:
        LOG.error("Error while connecting to MySQL" + str(e))
    except Exception as f:
        LOG.error(f)
    finally:
        # closing database connection.
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

        with open(skills_loc + "brandNames0911.txt", 'r+') as brandsFileIn:
            with open(i_like_loc + "BrandName.voc", 'w+') as brandsFileOut:
                lines = brandsFileIn.readlines()
                brandsFileOut.writelines(lines)

        with open(skills_loc + "brandNames0911.txt", 'r') as brandsFileIn:
            with open(i_like_loc + "brandname.entity", 'w+') as brandsFileOut:
                lines = brandsFileIn.readlines()
                brandsFileOut.writelines(lines)

        with open(skills_loc + 'TmpAudioBrandCoupons.csv', mode='rt+') as f,\
                open(skills_loc + 'NewAudioBrandCoupons.csv', 'w+', newline='') as final:
            writer2 = csv.writer(final, quoting=csv.QUOTE_ALL)
            reader = csv.reader(f, delimiter=',')
            sorted2 = sorted(reader, key=lambda line: str(line[0]))
            for row in sorted2:
                writer2.writerow(row)

        # LOG.debug('device = ' + device)
        with open(skills_loc + "brandNames0911.txt", 'r') as brandsFileIn:
            with open(brandscoupons_loc + "BrandName.voc", 'w') as brandsFileOut:
                lines = brandsFileIn.readlines()
                brandsFileOut.writelines(lines)

        with open(skills_loc + "brandNames0911.txt", 'r') as brandsFileIn:
            with open(brandscoupons_loc + "brandname.entity", 'w') as brandsFileOut:
                lines = brandsFileIn.readlines()
                brandsFileOut.writelines(lines)

        with open(skills_loc + 'TmpAudioBrandCoupons.csv', mode='rt') as f,\
                open(brandscoupons_loc + 'NewAudioBrandCoupons.csv', 'w', newline='') as final:
            writer2 = csv.writer(final, quoting=csv.QUOTE_ALL)
            reader = csv.reader(f, delimiter=',')
            sorted2 = sorted(reader, key=lambda line: str(line[0]))
            for row in sorted2:
                writer2.writerow(row)

        create_signal("ILC_updateSuccess")
        check_for_signal("ILC_updating")
        return brandscoupons_loc
