import os
from flask import Flask, jsonify, request
from mangum import Mangum
from asgiref.wsgi import WsgiToAsgi
from discord_interactions import verify_key_decorator
from verify_id import verify_id

DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")

app = Flask(__name__)
asgi_app = WsgiToAsgi(app)
handler = Mangum(asgi_app)


@app.route("/", methods=["POST"])
async def interactions():
    print(f"Request: {request.json}")
    raw_request = request.json
    return interact(raw_request)


@verify_key_decorator(DISCORD_PUBLIC_KEY)
def interact(raw_request):
    def make_response(message_content):
        return jsonify(
            {
                "type": 4,
                "data": {"content": message_content},
            }
        )

    if raw_request["type"] == 1:  # PING
        response_data = {"type": 1}  # PONG
    else:
        # Log the request
        print(raw_request)
        data = raw_request["data"]
        command_name = data["name"]

        if command_name == "verify":
            # Ensure the command is used in a DM properly
            # Do not want this being set up in a public channel
            if "guild_id" in raw_request:
                # Return the server warning letting the user know
                return make_response("This command cannot be used in a server")
            # Get info from request to pass to function
            verification_code = data["options"][0]["value"]
            channel_id = raw_request["channel_id"]
            # Verify will return the user's username if the verification was successful
            username = verify_id(verification_code, channel_id)

            if not username:
                return make_response("Invalid verification code")
            # User's accounts were connected successfully
            return make_response(
                f"Successfully connected this channel to recieve notifications for the tee time searches of {username}"
            )
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)
