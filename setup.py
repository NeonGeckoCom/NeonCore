# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
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

BASE_PATH = path.abspath(path.dirname(__file__))


with open(path.join(BASE_PATH, "neon_core",
                    "version.py"), "r", encoding="utf-8") as v:
    for line in v.readlines():
        if line.startswith("__version__"):
            if '"' in line:
                version = line.split('"')[1]
            else:
                version = line.split("'")[1]

with open(path.join(BASE_PATH, "README.md"), "r") as f:
    long_description = f.read()


def get_requirements(requirements_filename: str):
    requirements_file = path.join(BASE_PATH, "requirements",
                                  requirements_filename)
    with open(requirements_file, 'r', encoding='utf-8') as r:
        requirements = r.readlines()
    requirements = [r.strip() for r in requirements if r.strip() and
                    not r.strip().startswith("#")]

    for i in range(0, len(requirements)):
        r = requirements[i]
        if "@" in r:
            parts = [p.lower() if p.strip().startswith("git+http") else p
                     for p in r.split('@')]
            r = "@".join(parts)
            if getenv("GITHUB_TOKEN"):
                if "github.com" in r:
                    r = r.replace("github.com",
                                  f"{getenv('GITHUB_TOKEN')}@github.com")
            requirements[i] = r
    return requirements


setup(
    name='neon-core',
    version=version,
    license='NeonAI License v1.0',
    author='Neongecko',
    author_email='developers@neon.ai',
    url='https://github.com/NeonGeckoCom/NeonCore',
    description='Neon Core',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=get_requirements('requirements.txt'),
    extras_require={
        "core_modules": get_requirements("core_modules.txt"),
        "client": get_requirements("client.txt"),
        "server": get_requirements("server.txt"),
        "dev": get_requirements("dev.txt"),
        "local": get_requirements("local_speech_processing.txt"),
        "remote": get_requirements("remote_speech_processing.txt"),
        "vision": get_requirements("vision.txt"),
        "test": get_requirements("test.txt"),
        "pi": get_requirements("pi.txt"),
        "docker": get_requirements("docker.txt"),
        "skills_required": get_requirements("skills_required.txt"),
        "skills_essential": get_requirements("skills_essential.txt"),
        "skills_default": get_requirements("skills_default.txt"),
        "skills_extended": get_requirements("skills_extended.txt")
    },
    packages=find_packages(include=['neon_core*']),
    package_data={'neon_core': ['res/precise_models/*', 'res/snd/*',
                                'res/text/*/*.voc', 'res/text/*/*.dialog',
                                'res/ui/*.qml', 'res/ui/*.png', 'res/*',
                                'configuration/*']
                  },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'neon=neon_core.cli:neon_core_cli',
            # TODO: Deprecate below entrypoints
            'neon_skills_service=neon_core.skills.__main__:main',
            'neon-install-default-skills=neon_core.util.skill_utils:install_skills_default',
            'neon-upload-diagnostics=neon_core.util.diagnostic_utils:cli_send_diags',
            'neon-start=neon_core.run_neon:start_neon',
            'neon-stop=neon_core.run_neon:stop_neon'
        ]
    }
)
