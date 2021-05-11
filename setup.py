# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from setuptools import setup, find_packages
import os.path

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    """ Find the version of mycroft-core"""
    version = None
    version_file = os.path.join(BASEDIR, 'mycroft', 'version', '__init__.py')
    major, minor, build = (None, None, None)
    with open(version_file) as f:
        for line in f:
            if 'CORE_VERSION_MAJOR' in line:
                major = line.split('=')[1].strip()
            elif 'CORE_VERSION_MINOR' in line:
                minor = line.split('=')[1].strip()
            elif 'CORE_VERSION_BUILD' in line:
                build = line.split('=')[1].strip()

            if ((major and minor and build) or
                    '# END_VERSION_BLOCK' in line):
                break
    version = '.'.join([major, minor, build])

    return version


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


setup(
    name='neon-core',
    version=get_version(),
    license='NeonAI License v1.0',
    author='Neongecko',
    author_email='developers@neon.ai',
    url='https://github.com/NeonGeckoCom/NeonCore',
    description='Neon Core',
    install_requires=required('requirements.txt'),
    packages=find_packages(include=['mycroft*']),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'neon-messagebus=mycroft.messagebus.service.__main__:main',
            'neon-bus-monitor=mycroft.messagebus.__main__:main',
            'neon-skills=mycroft.skills.__main__:main',
            'neon-audio=mycroft.audio.__main__:main',  # TODO: Remove when #74 merged and audio extracted from core
            'neon-echo-observer=mycroft.messagebus.client.ws:echo',
            'neon-audio-test=mycroft.util.audio_test:main',
            'neon-gui-listener=mycroft.enclosure.__main__:main',
            'neon-start=mycroft.run_neon:start_neon',
            'neon-stop=mycroft.run_neon:stop_neon'
        ]
    }
)
