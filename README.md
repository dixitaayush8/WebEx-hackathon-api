# WebEx-hackathon-api
API endpoints to demo the features we want to integrate for the hackathon

1. One GET endpoint for getting the top invitee recommendations based on the meetings they had during the past month.

2. One POST endpoint to add a meeting, generate a room of all the invitees and host for that meeting, send a specific agenda to that room, and send pre-specified scheduled message alerts to host.


# Setup Instructions
1. Make sure you have Python 3.7+ installed. If you do not, make sure to download and install Python 3.7+.
2. After cloning this project, navigate to the project folder and run `pip install virtualenv` to install the virtual environment for Flask. (NOTE: If `pip` does not work for you, try `pip3`. Depending on how your system is set up, `pip` and `python` may be automatically configured for Python 2, while `python3` and `pip3` could be configured for Python 3. But make sure you are using Python 3 in all cases. You can verify this by doing `python --version` or `python3 --version`).
3. Run `virtual venv` to create a virtual environment.
4. To activate the virtual environment, do `source venv/bin/activate`.
5. To install all the necessary Python packages necessary to make this project run, do `pip install -r requirements.txt` (or `pip3 install -r requirements.txt`).
6. Go to https://developer.webex.com and log in using your Webex Teams account. 
7. Go to a random endpoint in the documentation (e.g. https://developer.webex.com/docs/api/v1/people/list-people) and copy your USER bearer token in the header. Note it down.
8. Click your profile -> "My Webex Apps" -> "Create a New App" -> "Create a Bot". You can call your bot name and username whatever you want. 
9. Copy your bot's non-expiring access token and note it down as your BOT bearer token.
10. Open `src/views.py` and paste your USER bearer token wherever you see "token for USER" (there are 3 instances). Paste your BOT bearer token wherever you see "BOT token" (one instance in the "send_alerts()" function). These are all in the headers of different endpoints. It should look like `Bearer <your token>`.
11. Navigate your terminal to the "src" folder. Do a `flask run`.
12. Your API is now set up and running. Go to the frontend code and set up your UI in another terminal. You will need both of these running at the same time. https://github.com/NavinaMathew/WebexUI.
