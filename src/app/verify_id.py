import os
import boto3
from botocore.exceptions import ClientError

VERIFY_TABLE = boto3.resource("dynamodb").Table("verification_code_table")
COGNITO_POOL = boto3.client("cognito-idp")


def check_in_table(verification_code: str):
    """Checks if the user's code is in the table"""
    print(f"Checking verification code in DynamoDB table")
    response = VERIFY_TABLE.get_item(Key={"verification_code": verification_code})
    # Handle the username not being in the table
    if "Item" not in response:
        print(f"Verification code not found in table")
        return ""
    print(f"Found username: {response['Item']['username']}")
    return response["Item"]["username"]


def update_user_attributes(user_pool_id, username, attribute_name, attribute_value):
    """Updates the user's attributes in the cognito pool"""
    print(f"Updating attribute {attribute_name} for user {username}")
    COGNITO_POOL.admin_update_user_attributes(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=[
            {"Name": attribute_name, "Value": attribute_value},
        ],
    )
    print(f"Successfully updated attribute")


def set_channel_id(username: str, channel_id: str):
    """Sets the channel id as a cognito attribute for the user"""
    print(f"Setting channel ID {channel_id} for user {username}")
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    custom_attribute_name = "custom:channel_id"
    custom_attribute_value = channel_id

    try:
        update_user_attributes(
            user_pool_id, username, custom_attribute_name, custom_attribute_value
        )
    except ClientError:
        print(f"Failed to update attribute, attempting to create it")
        # If the attribute does not already exist, create it
        COGNITO_POOL.admin_add_custom_attributes(
            UserPoolId=user_pool_id,
            CustomAttributes=[
                {"Name": custom_attribute_name, "AttributeDataType": "String"},
            ],
        )
        print("Created custom attribute in Cognito")
        # Retry setting the attribute
        update_user_attributes(
            user_pool_id, username, custom_attribute_name, custom_attribute_value
        )


def remove_verification_code(verification_code: str):
    """Removes the verification code from the table"""
    print(f"Removing verification code from table")
    # Function does not return a value
    VERIFY_TABLE.delete_item(Key={"verification_code": verification_code})
    print("Successfully removed verification code")


def verify_id(verification_code: str, channel_id: str):
    """Verifies the user's verification code"""
    print(f"Starting verification process for channel ID: {channel_id}")
    # Check if the verification code is in the table
    username = check_in_table(verification_code)
    if not username:
        print("Verification failed: invalid code")
        # If the verification code is not in the table, return an empty string
        return ""
    try:
        # Set the channel id as a cognito attribute for the user
        set_channel_id(username, channel_id)
        # Remove the verification code from the table to prevent code collisions
        remove_verification_code(verification_code)
        print(f"Verification successful for user: {username}")
        # Return cognito username to inDdicate success
        return username
    except Exception as e:
        print(f"Error during verification process: {str(e)}")
        return ""
