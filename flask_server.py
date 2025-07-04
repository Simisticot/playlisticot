import os
import flask
import requests

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

SECRETS_FILE = "client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtubepartner",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

app = flask.Flask(__name__)
app.secret_key = "yipeeeeeee"


@app.route("/")
def root():
    return "Hi"


@app.route("/make_cool_playlist")
def make_cool_playlist():
    if "creds" not in flask.session:
        return flask.redirect("authorize")
    else:
        creds = google.oauth2.credentials.Credentials(**flask.session["creds"])
        print(flask.session["creds"])
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
        youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": "MY VERY COOL PLAYLIST",
                    "description": "made via playlisticot",
                    "tags": ["sample playlist", "API call"],
                    "defaultLanguage": "en",
                },
                "status": {"privacyStatus": "private"},
            },
        ).execute()
    return "did it work ?"


@app.route("/authorize")
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        SECRETS_FILE, scopes=SCOPES
    )
    flow.redirect_uri = flask.url_for("callback", _external=True)
    authorization_url, state = flow.authorization_url(
        access_type="offline", include_granted_scopes="true"
    )
    flask.session["state"] = state

    return flask.redirect(authorization_url)


@app.route("/callback")
def callback():
    state = flask.session["state"]
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        SECRETS_FILE, scopes=SCOPES, state=state
    )
    flow.redirect_uri = flask.url_for("callback", _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    creds = flow.credentials

    flask.session["creds"] = credentials_to_dict(creds)

    return flask.redirect(flask.url_for("make_cool_playlist"))


def credentials_to_dict(credentials):
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "granted_scopes": credentials.granted_scopes,
    }


if __name__ == "__main__":
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # This disables the requested scopes and granted scopes check.
    # If users only grant partial request, the warning would not be thrown.
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run("localhost", 8800, debug=True)
