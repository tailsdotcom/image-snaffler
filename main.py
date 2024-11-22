import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
import datetime
import requests
logging.basicConfig(level=logging.INFO)

# WebClient insantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
# Store conversation history
conversation_history = []
# ID of the channel you want to send the message to
channel_id = "CFYT1NZDX"

try:
    # Call the conversations.history method using the WebClient
    # conversations.history returns the first 100 messages by default
    # These results are paginated, see: https://api.slack.com/methods/conversations.history$pagination
    result = client.conversations_history(channel=channel_id)

    conversation_history = result["messages"]

    # Print results
    logging.info("{} messages found in {}".format(len(conversation_history), id))

    for message in conversation_history:
        if "files" in message:
            for file in message["files"]:
                timestamp = file["timestamp"]
                timestring = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                filetype = file["filetype"]
                id = file["id"]
                logging.info(f"Found file {id} uploaded at {timestring} of type {filetype}")
                response = requests.get(file["url_private_download"])

                filename = f"./files/{id}.{filetype}"
                if os.path.isfile(filename):
                    logging.info(f"Skipping download file exists: {filename}")
                else:
                    with open(filename, "wb") as f:
                        f.write(response.content)

except SlackApiError as e:
    logging.error("Error creating conversation: {}".format(e))