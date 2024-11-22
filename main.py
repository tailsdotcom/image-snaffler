import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
import datetime
import requests
import sys

from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient.http import MediaInMemoryUpload
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]
logging.basicConfig(level=logging.INFO)
FOLDER = "16g-UygXMdIUGG4KqUMh4yFJ9OmOXaI4I"

# WebClient insantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)
# Store conversation history
conversation_history = []
# ID of the channel you want to send the message to
channel_id = "CFYT1NZDX"


def get_slack_files():
    try:
        # Call the conversations.history method using the WebClient
        # conversations.history returns the first 100 messages by default
        # These results are paginated, see: https://api.slack.com/methods/conversations.history$pagination
        result = client.conversations_history(channel=channel_id)

        conversation_history = result["messages"]

        # Print results
        logging.info(
            "{} messages found in {}".format(len(conversation_history), channel_id)
        )

        google_drive_file_list = get_file_list()

        for message in conversation_history:
            if "files" in message:
                for file in message["files"]:
                    timestamp = file["timestamp"]
                    timestring = datetime.datetime.fromtimestamp(timestamp).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    filetype = file["filetype"]
                    mimetype = file["mimetype"]
                    id = file["id"]
                    logging.info(
                        f"Found file {id} uploaded at {timestring} of type {filetype}"
                    )
                    headers = {"Authorization": "Bearer " + SLACK_BOT_TOKEN}
                    response = requests.get(file["url_private"], headers=headers)

                    filename = f"{id}.{filetype}"

                    if filename in google_drive_file_list:
                        logging.info(f"Skipping download file exists: {filename}")
                    else:
                        logging.info(f"Trying to upload file {filename}")
                        upload_file(filename, response.content, mimetype)
                    # if os.path.isfile(filename):
                    #     logging.info(f"Skipping download file exists: {filename}")
                    # else:
                    #     with open(filename, "wb") as f:
                    #         f.write(response.content)

    except SlackApiError as e:
        logging.error("Error creating conversation: {}".format(e))


def upload_file(file_name, content, mime_type):
    service_account_file = "./credentials.json"
    creds = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )

    service = discovery.build("drive", "v3", credentials=creds, cache_discovery=False)
    media_body = MediaInMemoryUpload(content, mimetype=mime_type)

    body = {
        "name": file_name,
        "title": file_name,
        "description": "",
        "mimeType": mime_type,
        "parents": [FOLDER],
    }

    # note that supportsAllDrives=True is required or else the file upload will fail
    file = (
        service.files()
        .create(supportsAllDrives=True, body=body, media_body=media_body)
        .execute()
    )


def get_file_list():
    service_account_file = "./credentials.json"
    creds = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES
    )
    try:
        service = discovery.build(
            "drive", "v3", credentials=creds, cache_discovery=False
        )

        items = []
        next_page_token = None
        while True:
            results = (
                service.files()
                .list(
                    q="'" + FOLDER + "' in parents",
                    pageSize=10,
                    pageToken=next_page_token,
                    fields="nextPageToken, files(id, name)",
                )
                .execute()
            )
            items = items + results.get("files", [])
            if "nextPageToken" in results:
                next_page_token = results["nextPageToken"]
            else:
                break

        file_list = []
        for item in items:
            file_list.append(item["name"])

        return file_list
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    get_slack_files()
