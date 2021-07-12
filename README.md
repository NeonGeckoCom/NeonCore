
# Table of Contents
1. [Forking Git Source](#1-forking-git-source)  
2. [Setting Up Service Accounts](#2-setting-up-service-accounts)  
   * [a. Google Cloud Speech](#a-google-cloud-speech-setup)  
   * [b. Amazon Polly and Translate](#b-amazon-polly-and-translate-setup)
3. [Setting Up Hardware](#3-setting-up-hardware)  
4. [Installing Neon](#4-installing-neon)  
   * [a. Development Environment](#a-installing-neon-in-a-development-environment)  
   * [b. User Environment](#b-installing-neon-in-a-userdeployment-environment)  
1. [Using Neon](#5-using-neon)  
   * [a. Running Tests](#a-running-tests)  
   * [b. Troubleshooting](#b-troubleshooting)  
1. [Making Changes](#6-making-changes)  
   * [a. System Overview](#a-system-overview)  
   * [b. Creating a Skill](#b-creating-a-skill)  
7. [Getting New Neon AI Releases](#7-getting-new-neon-ai-releases)  
7. [Removing and re-installing Neon](#8-reinstalling-neon)  

# Welcome to Neon AI
Neon AI is an open source voice assistant. Follow these instructions to start using Neon on your computer.

# 1. Forking Git Source
Before installing Neon, you will need to fork your own branch of the Neon
[core](https://github.com/NeonGeckoCom/shared-neon-core) and [skills] repositories on github. You will also need to get
`neonSetup.sh` from your forked core git.

1. Go to the [core repository](https://github.com/NeonGeckoCom/shared-neon-core) and click "Fork" in the upper right
hand corner.
   >![NeonDev](https://0000.us/klatchat/app/files/neon_images/git_setup_screens/Git1.png)

1. Select the account you wish to fork to (generally you only have one listed)

1. Do the same for the [skills repository](https://github.com/NeonGeckoCom/neon-skills-submodules)
   > *Note*: You may also wish to fork individual skills and update the submodule references in your forked repository.
   > You can find more information about submodules [here](https://git-scm.com/book/en/v2/Git-Tools-Submodules).

1. Locate `NGI\neonSetup.sh` in your `core` repository
   > ![NeonDev](https://0000.us/klatchat/app/files/neon_images/git_setup_screens/Git3.png)

5. Right Click on `Raw` and select `Save link as...`
   > ![NeonDev](https://0000.us/klatchat/app/files/neon_images/git_setup_screens/Git4_1.png)

6. Rename the file to neonSetup.sh and save to your `Home` directory 
   >  *Note*: If you completed this step on a Windows PC, save the file to a flash drive to transfer to the computer you
   >  will install Neon on. Move `neonSetup.sh` to a directory on the machine you will be installing on.
   >  Recommended `~/` (resolves to /home/`$USER`).


# 2. Setting Up Service Accounts
Please follow these steps to create the three credential files required to install Neon. During setup, all credentials 
will be imported and validated with any errors logged in `status.log`.
> *Note:* If you complete this setup on a Windows PC, make sure to edit any files using a text editor such as 
[Notepad++](https://notepad-plus-plus.org/) to ensure compatibility in Linux. Also check for correct file extensions 
after copying your files to your Linux PC, as Windows will hide known file extensions by default.


## a. Google Cloud Speech Setup
1. Go to: 
    > https://cloud.google.com/

1. Sign in or create a `Google account`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google1.png)


1. Go to your `Console`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google2.png)


1. Search for and select `"Cloud Speech-to-Text"` (Not to be confused with Text-to-Speech)
1. Select the option you would like to use
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google3.png)


1. You will be prompted to enable billing on your account at this point because this service is paid after a free monthly 
quota
    > Google will not automatically charge your card unless you give permission to do so. 
1. In the left `Navigation Menu`, select `APIs & Services`, `Credentials`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google4.png)


1. Click `Create credendials`, `Service Account Key`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google5.png)


1. Choose any service account name for your reference. You may leave the `Role` field empty
1. Make sure key type is `JSON` and click on `Continue`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google6.png)


1.  If you did not assign a role, you would be prompted. You may continue by clicking `'CREATE WITHOUT ROLE'`
    >![Google](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Google7.png)


1. You will see a prompt and your service key will automatically download
1. Rename the downloaded file to `google.json` and move it into the same directory as neonSetup.sh

    > *Note:* The premium models are only available in US English and provide some enhancements to phone and video audio 
    which do not apply to this project. The options with Data Logging allows Google to use your audio and transcriptions to 
    train their model. You may select the option without logging to opt out (note that the option with logging is 
    discounted).

At this point, Neon can be partially tested without `Amazon translations` and `Wolfram information` skills. You may run 
setup without continuing, but Amazon and Wolfram|Alpha services are *highly* recommended.


## b. Amazon Polly and Translate Setup
1. Go to: 
    > https://aws.amazon.com/

1. Click `"Sign into the Console"` at the top right of the screen
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon1.png)


1. Sign in or register for an account
1. Go to the `Services Menu` at the top left of the screen and click `IAM`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon2.png)


1. Select `Users` from the left side menu and click `Add user`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon3.png)


1. Enter a `User name` and check the box for `Programmatic access`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon4.png)


1. On the next page, Select `'Attach existing policies directly'` and search for `'AmazonPollyFullAccess'` and 
`'TranslateFullAccess'`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon5.png)
     ![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon6.png)


1. You may add tags on the next page if desired
1. Review your selections on the next page and `Create user`
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon7.png)


1. On the next page you can see your `Access key ID` and `Secret access key`
1. Click the `Download .csv file` button to save your credentials to your computer
    >![Amazon](https://0000.us/klatchat/app/files/neon_images/account_setup_screens/Amazon8.png)


1. Copy or move the downloaded `accessKeys.csv` to the same directory as neonSetup.sh

    > *Note:* You will ***not*** be able to view your secret access key after it is generated, so if you need a secret 
    access key, you will have to generate a new Access key.

The Users menu lets you create new users and new access keys per user as you wish, as well as modify permissions.

# 3. Setting Up Hardware
Before continuing, make sure you have your hardware setup ready for installation. You will need the following:
* A computer running up-to-date Ubuntu 20.04
  >   You can find our video tutorial for installing Ubuntu in a virtual machine 
  >   [here](https://neongecko.com/WindowsOptionUbuntuVirtualMachineInstall), or you can find written instructions
  >   [here](https://tutorials.ubuntu.com/tutorial/tutorial-install-ubuntu-desktop#0)
  
  > *Note:* If you prefer to use Windows for your development environment, you can install the
  > [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10). You can find our video
  > tutorial [here](https://neongecko.com/WindowsOptionSubsystemforLinux). Audio and gui functionality will be limited
  > in this case; you will only be able to interact with Neon via command line.

## System Requirements
* Speakers and a microphone recognized by Ubuntu
    >![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Setup1.png)
     You can verify Ubuntu sees your devices by accessing `Settings` and then `Sound`
    * If you are unsure of which device to select, you can click `Test Speakers` to play a test tone through the selected 
    Output device
    * You can test your microphone under the `Input` tab, the Input level should move when you speak into the microphone
        > If you do not see any microphone activity, make sure the correct device is selected and the Input volume is set 
          above 50%

* Webcam (optional)
    > Some functionality requires a webcam (ex. USB Cam Skill). Most webcams also include a microphone that can be used 
    for Neon.

* An active internet connection
  >   *Note*: A connection of at least 10Mbps is recommended. On slower connections, installation may take several
  >   hours.

* At least `10GB` of available disk space (`15 GB` if installing Mimic)
  > Neon AI occupies less than 1GB itself. With dependencies, the installation takes about 5GB on an up-to-date Ubuntu
  > 20.04 system. Mimic local speech-to-text requires about 3.5 GB. Additional space is used while installing packages 
  > during installation and updates. Several gigabytes is recommended in order to keep local transcriptions and audio files.

* A system with at least 2GB RAM and 2 or more processing threads is required, with 4GB RAM and 4 threads recommended
  > Some features such as the vision service may not work on systems only meeting the minimum requirements. Responses 
  > and speech processing will take longer on lower performance systems.

# 4. Installing Neon
This guide includes instructions for installing in both a Development environment and a User environment. User 
environment is more lightweight and does not assume any existing IDE. Developer environment will have more consoles, 
debug outputs, and logs available. See details below. 

A development environment is designed to be a testable installation of NeonAI that can be connected to an IDE   
(ex. Pycharm) for modifications and skill development. This guide assumes installation in a development environment from 
an unmodified fork of NeonAI. After installation, any changes and additions can be pushed to git or hosted on a private 
server.  
  
A user environment is designed to be an installation on a device that will be used normally as a voice assistant. You
may want to test how your changes affect performance on less powerful hardware or test how changes may be deployed as
updates.  
If you are developing in a virtual machine, installation on physical hardware in a user environment is useful for
testing audio and video I/O which can be difficult in many virtualized environments.  

Before starting here, make sure you have already completed
[setting up your service accounts](#setting-up-service-accounts). You should have `google.json`,
`wolfram.txt`, and `accessKeys.csv` already saved to the machine you are installing to.


All of the following options, such as autorun and automatic updates can be easily modified later using your voice,
profile settings, or configuration files.
  
## Installing Neon in a Development Environment  

1. Clone NeonCore from your forked repository into a local directory.
1. Configure a virtual environment and install any desired requirements
  >*Note*: `requirements.txt`,`dev.txt`, `test.txt`, and `remote_speech_processing.txt` are recommended for installation
  
## Installing Neon in a User/Deployment Environment  
Installing in a User Environment differs from a developer environment; you will not be able to modify Neon Core if you 
use this installation method.
  
1. Take your `setup.sh` file and place it in your home directory  
    >![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Neon1.png)  
1. Make sure you have your `accessKeys.csv`, `google.json`, and `wolfram.txt` files here as well, otherwise you will be 
   prompted for credentials during setup  
1. Open a terminal in your home directory (`ctrl`+`alt`+`t`)  
1. Type in `bash setup.sh ${GITHUB_TOKEN}` and press `Enter` (where `${GITHUB_TOKEN}` is your Github token)
   >![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Neon2.png)  
1. Type `n` to Install in User Mode (Not Developer Mode)
1. Type `n` to Input Custom settings
    >*Note*: You may use quick settings and skip the following prompts
___
8. Type `n` to install in User mode  (`y` for full Developer mode)
8. `Autorun` is recommended (`y`) on for User Environments  
8. `Automatic updates` are recommended (`y`) on for User Environments  
8. `Local STT` is NOT recommended (`n`) if you have google and aws keys as remote processing is faster and more accurate 
8. `Install GUI` is recommended (`y`) so long as you are running a current/supported version of Ubuntu and your device
   has a display
8. Find out more about OpenHAB [here](https://www.openhab.org/docs/)  
14. `Server` is NOT recommended (`n`) unless you know otherwise 
    
1. You will be prompted to confirm your settings, press `y` to continue, `n` to start over, or `b` to go back and 
   correct a previous setting
   > ![NeonDev](https://0000.us/klatchat/app/files/neon_images/neon_setup_screens/Neon3-1.png)
   
1. When setup is complete, you will be able to start neon via `start_neon.sh`
  
# 5. Using Neon  
After you have completed [Installing Neon](#installing-neon), you will have a fully functional system ready to test.
A useful first step after a new installation or update is to run an automated test of your skills.

## a. Running Tests
1. With Neon running, use the desktop shortcut `Test Neon` or File menu option `Run Tests` to run tests
    >![TestNeon](https://0000.us/klatchat/app/files/neon_images/test_neon_screens/Test1.png)
    
1. The test program will automatically backup your user settings and run a network speed test and then present you with 
the test options
    >![TestNeon](https://0000.us/klatchat/app/files/neon_images/test_neon_screens/Test2.png)
    
    >
    >  The upper case options determine the way testing is run (Text or Audio).  
    >  The lower case options determine which skills are tested.

1. Type in the options you wish to test with, you may string multiple together (ex. `TaAa` would run all tests as Text 
and then all tests as Audio)
   >  *Note*: If running audio tests, you must loop back audio output to audio input (the easiest way to do this is to
   >  run a 3.5mm cable from your speaker port to your microphone port)

1. After selecting your options and pressing `Enter`, you will see the test pass either text or audio to Neon.
    >![TestNeon](https://0000.us/klatchat/app/files/neon_images/test_neon_screens/Test3.png)
    
1. The `System Monitor` will show available statistics such as CPU Utilization, Temperature, and Power
    > *Note*: This data is saved with test results
    
1. After the tests have completed, Neon will restart and you will see an option to review test results. The results are 
saved as `Tab` separated values, so make sure only the `Tab` option is selected.
    >![TestNeon](https://0000.us/klatchat/app/files/neon_images/test_neon_screens/Test4.png)

1. More complete logs and information can be found in the Diagnostics directory
    >By default, this is at `~\NeonAI\Diagnostics\testing` for Development Machines and
     `~\Documents\NeonGecko\Diagnostics\testing` for User Machines.
     
## b. Troubleshooting
If you encounter any of the following issues while using Neon, please try these troubleshooting steps

* My computer is slow to respond
  > Check for high memory usage in `System Monitor`. If your Memory and Swap both show 100% utilization under
  > `Resources`, try exiting PyCharm and Neon AI. If there is still abnormal memory usage, open a Terminal and type in:
  ```bash
    sudo systemctl stop openhab2.service
   ```  
  > If you can determine the offending program, see if restarting the program or your computer resolves your issues. If
  > not, you may find common solutions online.
  
* Neon AI is not transcribing anything I say
  >   Check that your microphone is working and active by going to `Sound` the `Settings` Menu. Go to the `Input` tab
  >   and make sure the correct microphone is selected. Make sure the `Input Level` is up and turned on and look for
  >   activity on the `Input Level` bar when you tap the mic. If you change devices here, restart Neon AI.

* Some audio is very quiet, while other audio is louder
  >   Check that the audio level for the affected application is turned up by going to `Sound` the `Settings` Menu. Go to
  >   the `Applications` tab.
   
  >   For quiet responses from Neon, ask Neon something with a longer response (ex. "Tell me a joke"). When an
  >   application named `neon-voice` appears, make sure it is not muted and that the volume is set to the maximum. Do
  >   the same for any other applications that are too quiet; start playing something and check the Application's
  >   volume.

* AVMusic will not pause or resume
  >   If AVMusic playback is changed by something other than Neon, the skill can lose track of whether something is
  >   playing or paused. If something is paused and Neon will not resume, you may say "pause" to resume playback. "Stop"
  >   should work in any case.
  
* Errors in the log when installing or updating Neon
  >   Installation of dlib can fail if system memory is completely full; you can open System Monitor during installation
  >   or updates to monitor memory usage. A minimum 2GB RAM is required, 4GB+ recommended. Errors may also occur if system
  >   storage becomes full. You may monitor storage availability in System Monitor as well; keep in mind that cached files
  >   will be removed when installation fails, so your file system will show some available space before and after the 
  >   error occurs.
  
* Any other issues
  >   If you encounter any other issues while using Neon, they can often be solved by restarting Neon or your computer.
  >   If this does not resolve you issue, please contact support at [info@neongecko.com](mailto:info@neongecko.com).

# 6. Making Code Changes
After completing setup and testing, you are ready to begin making changes and creating skills. An example workflow for 
making a change would be:

1. Make any changes to the `core` or `skills`
1. Test changes in the Developer Environment (Look for errors in logs, unexpected behaviour, etc)
1. Run `Test Neon` to check that all skills and TTS/STT behave as expected
1. Commit and Push changes to git
1. Check for updates in User Environment
1. Run complete tests using `Test Neon`
1. Check logs for any errors

## a. System Overview
There are two aspects of the Neon AI system: `core` and `skills`.

The `core` is composed of several modules, but generally includes:
  - `speech` for handling user inputs and performing speech-to-text (STT)
  - `skills` for processing user input to find intent and provide a response
  - `audio` for speaking the response generated in skills
  - `bus` for handling all communications between modules

Other modules may also be running for gui functionality, etc and may be added to provide new functionality.

`skills` provide the functionality of handling user inputs and generating responses or performing actions. 


## b. Creating a Skill
Check out our three part youtube series on how to create a skill:
https://youtu.be/fxg25MaxIcE
https://youtu.be/DVSroqv6E6k
https://youtu.be/R_3Q-P3pk8o

# 7. Getting New Neon AI Releases
Neongecko will regularly release updates to the Neon core and skills via GitHub. It is recommended that you merge these
updates into your own fork so that you get the latest feature updates and bug fixes. To update your repository to the
latest release:

1. Go to [GitHub](https://github.com) and sign in.
2. Go to the Neongecko [neon-shared-core repository](https://github.com/NeonGeckoCom/neon-shared-core).
   > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease1.png)
3. Open a `New pull request`
4. Click `compare across forks`
5. Select your forked repository from the `base repository` drop-down on the left
   > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease2.png)
6. You may modify the pull request title and description (optional)
   > *Note*: All changes are displayed per file on this page. You may want to change the title for your own reference
   > later.
7. Click `Create pull request` after you have reviewed the changes
8. Click `Merge pull request` on the next page to finish merging the changes to your branch
   > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease3.png)
9. Go to the Neongecko [neon-skills-submodules](https://github.com/NeonGeckoCom/neon-skills-submodules) and repeat
   the above steps to update your skills
   > *Note*: If you have modified your forked submodules repository, you may want to update the submodules in your repository
   > instead of pulling changes here. You can find more information about submodules 
   > [here](https://git-scm.com/book/en/v2/Git-Tools-Submodules).
9.  You are now using the latest release of Neon AI, make sure to update any installations if they are not set to update
    automatically
10. Use the desktop shortcut `Update Neon` or File menu option `Check for Updates` to update Neon
    >![TestNeon](https://0000.us/klatchat/app/files/neon_images/test_neon_screens/Test1.png)

## Additional Steps for Developers Using PyCharm
11. Next you should update your IDE in your Developer Environment
>    *Note*: This is PyCharm if you followed our setup guide.
10. In PyCharm, select `VCS` from the menu bar, and then `Update Project`
    > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease4.png)
11. You will be prompted to `Update Project`, you may leave the default settings and click `OK`
    > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease5.png)



# 8. Removing and Re-installing Neon AI
You may wish to remove your Neon AI installation to start fresh with a new version. Below is a list of locaitons
where Neon may have saved files:
   > *Note:* You will need your credential files for Google, Amazon, and Wolfram|Alpha to complete re-installation.
  - `~/.neon`
  - `~/.local/share/neon`
  - `~/.local/cache/neon`
  - `/opt/neon`
  - `/tmp/neon`
  - `~/Documents/NeonGecko`
  - `~/Pictures/NeonGecko`
  - `~/Videos/NeonGecko`
  - `~/Music/NeonGecko`


5. You may now [re-install Neon](#4-installing-neon)
