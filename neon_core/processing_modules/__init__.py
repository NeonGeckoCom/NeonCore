# # NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# # All trademark and other rights reserved by their respective owners
# # Copyright 2008-2021 Neongecko.com Inc.
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

from threading import Thread, Event
from os.path import join, basename
import os
import time
import sys
import gc
from glob import glob
import imp
from mycroft.util.log import LOG

DEBUG = True

MainModule = '__init__'


def _get_last_modified_date(path):
    """
        Get last modified date excluding compiled python files, hidden
        directories and the settings.json file.

        Args:
            path:   skill directory to check

        Returns:
            int: time of last change
    """
    all_files = []
    for root_dir, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if (not f.endswith('.pyc') and f != 'settings.json' and
                    not f.startswith('.')):
                all_files.append(join(root_dir, f))
    # check files of interest in the skill root directory
    return max(os.path.getmtime(f) for f in all_files)


class ModuleLoaderService(Thread):
    def __init__(self, bus, modules_dir):
        super(ModuleLoaderService, self).__init__()
        self._stop_event = Event()
        self.loaded_modules = {}
        self.has_loaded = False
        self.bus = bus
        self.modules_dir = modules_dir
        self.blacklist = []

    @staticmethod
    def load_module(module_descriptor, module_name, blacklist=None, bus=None):
        """ Load module from module descriptor.

        Args:
            module_descriptor: descriptor of module to load
            module_name:       name for module

        Returns:
            Parser: the loaded module or None on failure
        """
        blacklist = blacklist or []
        path = module_descriptor["path"]
        name = basename(path)
        LOG.info("ATTEMPTING TO LOAD PARSER: {} with ID {}".format(
            name, module_name
        ))
        if name in blacklist or path in blacklist:
            LOG.info("PARSER IS BLACKLISTED " + name)
            return None
        main_file = join(path, MainModule + '.py')
        try:
            with open(main_file, 'rb') as fp:
                module_module = imp.load_module(name.replace('.', '_'), fp,
                                                main_file, ('.py', 'rb',
                                                            imp.PY_SOURCE))

            LOG.info("Loading " + name)
            if (hasattr(module_module, 'create_module') and
                    callable(module_module.create_module)):
                module = module_module.create_module()
                try:
                    module.bind(bus)
                    module.initialize()
                except Exception as e:
                    # If an exception occurs, make sure to clean up the module
                    module.default_shutdown()
                    raise e

                LOG.info("Loaded " + name)
                return module
            else:
                LOG.warning("Module {} does not appear to be a module".format(
                    name))
        except Exception:
            LOG.exception("Failed to load module: " + name)
        return None

    @staticmethod
    def create_module_descriptor(module_path):
        return {"path": module_path}

    def run(self):
        # Scan the file folder that contains Parsers.  If a Parser is
        # updated, unload the existing version from memory and reload from
        # the disk.
        while not self._stop_event.is_set():

            # Look for recently changed module(s) needing a reload
            # checking modules dir and getting all modules there
            module_paths = glob(join(self.modules_dir, '*/'))
            still_loading = False
            for module_path in module_paths:
                still_loading = (
                        self._load_module(module_path) or
                        still_loading
                )
            if not self.has_loaded and not still_loading and \
                    len(module_paths) > 0:
                self.has_loaded = True

            self._unload_removed(module_paths)

            time.sleep(1)  # sleep briefly

    def stop(self):
        """ Tell the manager to shutdown """
        self._stop_event.set()

    @property
    def modules(self):
        # return a list of modules ordered by priority
        modules = []
        for module in self.loaded_modules:
            instance = self.loaded_modules[module].get("instance")
            if instance:
                modules.append((module, instance.priority))
        modules = sorted(modules, key=lambda kw: kw[1])
        return [p[0] for p in modules]

    def get_module(self, module):
        return self.loaded_modules[module].get("instance")

    def _load_module(self, module_path):
        """
            Check if unloaded module or changed module needs reloading
            and perform loading if necessary.

            Returns True if the module was loaded/reloaded
        """
        module_path = module_path.rstrip('/')
        module = self.loaded_modules.setdefault(module_path, {})
        module.update({
            "id": basename(module_path),
            "path": module_path
        })

        # check if folder is a module (must have __init__.py)
        if not MainModule + ".py" in os.listdir(module_path):
            return False

        # getting the newest modified date of module
        modified = _get_last_modified_date(module_path)
        last_mod = module.get("last_modified", 0)

        # checking if module is loaded and hasn't been modified on disk
        if module.get("loaded") and modified <= last_mod:
            return False  # Nothing to do!

        # check if module was modified
        elif module.get("instance") and modified > last_mod:

            LOG.debug("Reloading Parser: " + basename(module_path))
            # removing listeners and stopping threads
            try:
                module["instance"].default_shutdown()
            except Exception:
                LOG.exception("An error occurred while shutting down {}"
                              .format(module["instance"].name))

            if DEBUG:
                gc.collect()  # Collect garbage to remove false references
                # Remove two local references that are known
                refs = sys.getrefcount(module["instance"]) - 2
                if refs > 0:
                    msg = ("After shutdown of {} there are still "
                           "{} references remaining. The module "
                           "won't be cleaned from memory.")
                    LOG.warning(msg.format(module['instance'].name, refs))
            del module["instance"]

        module["loaded"] = True
        desc = self.create_module_descriptor(module_path)
        module["instance"] = self.load_module(desc, module["id"],
                                              blacklist=self.blacklist,
                                              bus=self.bus)
        module["last_modified"] = modified
        if module['instance'] is not None:
            return True
        return False

    def _unload_removed(self, paths):
        """ Shutdown removed modules.

            Arguments:
                paths: list of current directories in the modules folder
        """
        paths = [p.rstrip('/') for p in paths]
        modules = self.loaded_modules
        # Find loaded skills that doesn't exist on disk
        removed_modules = [str(s) for s in modules.keys() if
                            str(s) not in paths]
        for s in removed_modules:
            LOG.info('removing {}'.format(s))
            try:
                LOG.debug('Removing: {}'.format(modules[s]))
                modules[s]['instance'].default_shutdown()
            except Exception as e:
                LOG.exception(e)
            self.loaded_modules.pop(s)

    def shutdown(self):
        self.stop()
