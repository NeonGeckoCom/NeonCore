from threading import Thread, Event
from os.path import join, dirname, basename
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


def load_parser(parser_descriptor, parser_name,
                BLACKLISTED_PARSERS=None, bus=None):
    """ Load parser from parser descriptor.

    Args:
        parser_descriptor: descriptor of parser to load
        parser_name:       name for parser

    Returns:
        Parser: the loaded parser or None on failure
    """
    BLACKLISTED_PARSERS = BLACKLISTED_PARSERS or []
    path = parser_descriptor["path"]
    name = basename(path)
    LOG.info("ATTEMPTING TO LOAD PARSER: {} with ID {}".format(
        name, parser_name
    ))
    if name in BLACKLISTED_PARSERS or path in BLACKLISTED_PARSERS:
        LOG.info("PARSER IS BLACKLISTED " + name)
        return None
    main_file = join(path, MainModule + '.py')
    try:
        with open(main_file, 'rb') as fp:
            parser_module = imp.load_module(name.replace('.', '_'), fp,
                                             main_file, ('.py', 'rb',
                                                         imp.PY_SOURCE))

        LOG.info("Loading " + name)
        if (hasattr(parser_module, 'create_parser') and
                callable(parser_module.create_parser)):
            parser = parser_module.create_parser()
            try:
                parser.bind(bus)
                parser.initialize()
            except Exception as e:
                # If an exception occurs, make sure to clean up the parser
                parser.default_shutdown()
                raise e

            LOG.info("Loaded " + name)
            return parser
        else:
            LOG.warning("Module {} does not appear to be a parser".format(
                name))
    except Exception:
        LOG.exception("Failed to load parser: " + name)
    return None


def create_parser_descriptor(parser_path):
    return {"path": parser_path}


class TextParsersService(Thread):
    parsers_dir = join(dirname(__file__), "modules").rstrip("/")

    def __init__(self, bus):
        super(TextParsersService, self).__init__()
        self._stop_event = Event()
        self.loaded_parsers = {}
        self.has_loaded = False
        self.bus = bus

    def run(self):
        # Scan the file folder that contains Parsers.  If a Parser is
        # updated, unload the existing version from memory and reload from
        # the disk.
        while not self._stop_event.is_set():

            # Look for recently changed parser(s) needing a reload
            # checking parsers dir and getting all parsers there
            parser_paths = glob(join(self.parsers_dir, '*/'))
            still_loading = False
            for parser_path in parser_paths:
                still_loading = (
                        self._load_parser(parser_path) or
                        still_loading
                )
            if not self.has_loaded and not still_loading and \
                    len(parser_paths) > 0:
                self.has_loaded = True

            self._unload_removed(parser_paths)

            time.sleep(1)  # sleep briefly

    def stop(self):
        """ Tell the manager to shutdown """
        self._stop_event.set()

    @property
    def parsers(self):
        # return a list of parsers ordered by priority
        parsers = []
        for parser in self.loaded_parsers:
            instance = self.loaded_parsers[parser].get("instance")
            if instance:
                parsers.append((parser, instance.priority))
        parsers = sorted(parsers, key=lambda kw: kw[1])
        return [p[0] for p in parsers]

    def parse(self, parser, utterances=None, user=None, lang="en-us"):
        utterances = utterances or []
        if parser in self.loaded_parsers:
            instance = self.loaded_parsers[parser].get("instance")
            if instance:
                return instance.parse(utterances, user, lang)
        return utterances, {}

    def _load_parser(self, parser_path):
        """
            Check if unloaded parser or changed parser needs reloading
            and perform loading if necessary.

            Returns True if the parser was loaded/reloaded
        """
        parser_path = parser_path.rstrip('/')
        parser = self.loaded_parsers.setdefault(parser_path, {})
        parser.update({
            "id": basename(parser_path),
            "path": parser_path
        })

        # check if folder is a parser (must have __init__.py)
        if not MainModule + ".py" in os.listdir(parser_path):
            return False

        # getting the newest modified date of parser
        modified = _get_last_modified_date(parser_path)
        last_mod = parser.get("last_modified", 0)

        # checking if parser is loaded and hasn't been modified on disk
        if parser.get("loaded") and modified <= last_mod:
            return False  # Nothing to do!

        # check if parser was modified
        elif parser.get("instance") and modified > last_mod:

            LOG.debug("Reloading Parser: " + basename(parser_path))
            # removing listeners and stopping threads
            try:
                parser["instance"].default_shutdown()
            except Exception:
                LOG.exception("An error occurred while shutting down {}"
                              .format(parser["instance"].name))

            if DEBUG:
                gc.collect()  # Collect garbage to remove false references
                # Remove two local references that are known
                refs = sys.getrefcount(parser["instance"]) - 2
                if refs > 0:
                    msg = ("After shutdown of {} there are still "
                           "{} references remaining. The parser "
                           "won't be cleaned from memory.")
                    LOG.warning(msg.format(parser['instance'].name, refs))
            del parser["instance"]

        parser["loaded"] = True
        desc = create_parser_descriptor(parser_path)
        parser["instance"] = load_parser(desc, parser["id"], bus=self.bus)
        parser["last_modified"] = modified
        if parser['instance'] is not None:
            return True
        return False

    def _unload_removed(self, paths):
        """ Shutdown removed parsers.

            Arguments:
                paths: list of current directories in the parsers folder
        """
        paths = [p.rstrip('/') for p in paths]
        parsers = self.loaded_parsers
        # Find loaded skills that doesn't exist on disk
        removed_parsers = [str(s) for s in parsers.keys() if
                            str(s) not in paths]
        for s in removed_parsers:
            LOG.info('removing {}'.format(s))
            try:
                LOG.debug('Removing: {}'.format(parsers[s]))
                parsers[s]['instance'].default_shutdown()
            except Exception as e:
                LOG.exception(e)
            self.loaded_parsers.pop(s)

    def shutdown(self):
        self.stop()
