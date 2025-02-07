import os
import boto3
from botocore.exceptions import ClientError

VERIFY_TABLE = boto3.resource("dynamodb").Table("verification_code_table")
COGNITO_POOL = boto3.client("cognito-idp")


def check_in_table(verification_code: str):
    """Checks if the user's code is in the table"""
    response = VERIFY_TABLE.get_item(Key={"verification_code": verification_code})
    # Handle the username not being in the table
    if "Item" not in response:
        return ""
    return response["Item"]["username"]


def update_user_attributes(user_pool_id, username, attribute_name, attribute_value):
    """Updates the user's attributes in the cognito pool"""
    COGNITO_POOL.admin_update_user_attributes(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=[
            {"Name": attribute_name, "Value": attribute_value},
        ],
    )


def set_channel_id(username: str, channel_id: str):
    """Sets the channel id as a cognito attribute for the user"""
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    custom_attribute_name = "custom:channel_id"
    custom_attribute_value = channel_id

    try:
        update_user_attributes(
            user_pool_id, username, custom_attribute_name, custom_attribute_value
        )
    except ClientError:
        # If the attribute does not already exist, create it
        COGNITO_POOL.admin_add_custom_attributes(
            UserPoolId=user_pool_id,
            CustomAttributes=[
                {"Name": custom_attribute_name, "AttributeDataType": "String"},
            ],
        )
        # Retry setting the attribute
        update_user_attributes(
            user_pool_id, username, custom_attribute_name, custom_attribute_value
        )
    else:
        raise ClientError


def remove_verification_code(verification_code: str):
    """Removes the verification code from the table"""
    # Function does not return a value
    VERIFY_TABLE.delete_item(Key={"verification_code": verification_code})


def verify_id(verification_code: str, channel_id: str):
    """Verifies the user's verification code"""
    # Check if the verification code is in the table
    username = check_in_table(verification_code)
    if not username:
        # If the verification code is not in the table, return an empty string
        return ""
    # Set the channel id as a cognito attribute for the user
    set_channel_id(username, channel_id)
    # Remove the verification code from the table to prevent code collisions
    remove_verification_code(verification_code)
    # Return cognito username to inDdicate success
    return username
