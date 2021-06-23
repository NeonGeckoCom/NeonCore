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
from os import path, getenv

BASEDIR = path.abspath(path.dirname(__file__))


def get_version():
    """ Find the version of mycroft-core"""
    version = None
    version_file = path.join(BASEDIR, 'version.py')
    with open(version_file) as f:
        for line in f:
            if '__version__' in line:
                version = line.split('=')[1].strip()
    return version


def get_requirements(requirements_filename: str):
    requirements_file = path.join(path.abspath(path.dirname(__file__)), "requirements", requirements_filename)
    with open(requirements_file, 'r', encoding='utf-8') as r:
        requirements = r.readlines()
    requirements = [r.strip() for r in requirements if r.strip() and not r.strip().startswith("#")]

    for i in range(0, len(requirements)):
        r = requirements[i]
        if "@" in r:
            parts = [p.lower() if p.strip().startswith("git+http") else p for p in r.split('@')]
            r = "@".join(parts)
            if getenv("GITHUB_TOKEN"):
                if "github.com" in r:
                    r = r.replace("github.com", f"{getenv('GITHUB_TOKEN')}@github.com")
            requirements[i] = r
    return requirements


setup(
    name='neon-core',
    version=get_version(),
    license='NeonAI License v1.0',
    author='Neongecko',
    author_email='developers@neon.ai',
    url='https://github.com/NeonGeckoCom/NeonCore',
    description='Neon Core',
    install_requires=get_requirements('requirements.txt'),
    extras_require={
        "client": get_requirements("client.txt"),
        "server": get_requirements("server.txt"),
        "dev": get_requirements("dev.txt"),
        "local": get_requirements("local_speech_processing.txt"),
        "remote": get_requirements("remote_speech_processing.txt"),
        "vision": get_requirements("vision.txt"),
        "test": get_requirements("test.txt")
    },
    packages=find_packages(include=['neon_core*']),
    package_data={'neon_core': ['res/precise_models/*', 'res/snd/*', 'res/text/*/*.voc', 'res/text/*/*.dialog',
                                'res/ui/*.qml', 'res/ui/*.png', 'res/*', 'configuration/*.conf']
                  },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'neon-messagebus=neon_core.messagebus.service.__main__:main',
            'neon-skills=neon_core.skills.__main__:main',
            'neon-install-default-skills=neon_core.util.skill_utils:install_skills_default'
            'neon-start=neon_core.run_neon:start_neon',
            'neon-stop=neon_core.run_neon:stop_neon'
        ]
    }
)
