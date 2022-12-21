[Optional Service Account Setup](#optional-service-account-setup)  
  * [a. Google Cloud Speech](#a-google-cloud-speech-setup)  
  * [b. Amazon Polly and Translate](#b-amazon-polly-and-translate-setup)

# Optional Service Account Setup
There are several online services that may be used with Neon. Speech-to-Text (STT) and Text-to-Speech (TTS) may be run 
locally, but remote implementations are often faster and more accurate. Following are some instructions for getting 
access to Google STT and Amazon Polly TTS. During setup, these credentials will be imported and validated.
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
