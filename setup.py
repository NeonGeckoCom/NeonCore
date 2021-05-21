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


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]


setup(
    name='neon-core',
    version="2021.5.6a12",
    license='Apache-2.0',
    author='NeonGecko',
    author_email='devs@mycroft.ai',
    url='https://github.com/MycroftAI/mycroft-core',
    description='NeonCore',
    install_requires=required('requirements.txt'),
    packages=find_packages(include=['neon_core*']),
    package_data={'': ['*.voc', '*.dialog', '*.qml', '*.mp3', '*.wav']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'neon-messagebus=neon_core.messagebus.service.__main__:main',
            'neon-bus-monitor=neon_core.messagebus.__main__:main',
            'neon-skills=neon_core.skills.__main__:main',
            'neon-audio=neon_core.audio.__main__:main',
            'neon-gui-listener=neon_core.enclosure.__main__:main'
        ]
    }
)
