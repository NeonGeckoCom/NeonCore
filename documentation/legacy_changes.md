[Making Changes](#making-code-changes)  
    * [a. System Overview](#a-system-overview)  
    * [b. Creating a Skill](#b-creating-a-skill)   

# Making Code Changes
After completing setup and testing, you are ready to begin making changes and creating skills. An example workflow for 
making a change would be:

1. Create or modify a skill
1. Test changes in the Developer Environment (Look for errors in logs, unexpected behaviour, etc.)
1. Run `Test Neon` to check that all skills and TTS/STT behave as expected
1. Commit and Push changes to git (for collaborative development, it is often best to create a new branch for any changes)
1. Install your updated skill in a User Environment (check for any missing dependencies, invalid file paths, etc.)
1. Run complete tests using `Test Neon`
1. Check logs for any errors

## a. System Overview
There are two aspects of the Neon AI system: `core` and `skills`.

The `core` is composed of several modules, but generally includes:
  - `speech` for handling user inputs and performing speech-to-text (STT)
  - `skills` for processing user input to find intent and provide a response
  - `audio` for speaking the response generated in skills
  - `bus` for handling all communications between modules
  - `enclosure` for handling any hardware interactions like speakers, microphone, lights, and buttons

Other modules may also be running for gui functionality, etc and may be added to provide new functionality.

`skills` provide the functionality of handling user inputs and generating responses or performing actions. 


## b. Creating a Skill
Check out our three part youtube series on how to create a skill:
https://youtu.be/fxg25MaxIcE
https://youtu.be/DVSroqv6E6k
https://youtu.be/R_3Q-P3pk8o

## Additional Steps for Developers Using PyCharm
11. Next you should update your IDE in your Developer Environment
>    *Note*: This is PyCharm if you followed our setup guide.
10. In PyCharm, select `VCS` from the menu bar, and then `Update Project`
    > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease4.png)
11. You will be prompted to `Update Project`, you may leave the default settings and click `OK`
    > ![NewRelease](https://0000.us/klatchat/app/files/neon_images/neon_release_screens/NewRelease5.png)
