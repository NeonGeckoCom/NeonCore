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

from setuptools import setup, find_packages
import os.path

BASEDIR = os.path.abspath(os.path.dirname(__file__))


def get_version():
    """ Find the version of mycroft-core"""
    version = None
    version_file = os.path.join(BASEDIR, 'version.py')
    with open(version_file) as f:
        for line in f:
            if '__version__' in line:
                version = line.split('=')[1].strip()
    return version


def required(requirements_file):
    """ Read requirements file and remove comments and empty lines. """
    with open(os.path.join(BASEDIR, "requirements", requirements_file), 'r') as f:
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
    extras_require={
        "client": required("client.txt"),
        "server": required("server.txt"),
        "dev": required("dev.txt"),
        "local": required("local_speech_processing.txt"),
        "remote": required("remote_speech_processing.txt"),
        "vision": required("vision.txt"),
        "test": required("extras.txt")
    },
    packages=find_packages(include=['neon_core*']),
    package_data={'neon_core': ['res/precise_models/*', 'res/snd/*', 'res/text/*/*.voc', 'res/text/*/*.dialog',
                                'res/ui/*.qml', 'res/ui/*.png', 'res/*', 'configuration/*.conf']
                  },
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
