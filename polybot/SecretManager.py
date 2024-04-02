import json
import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secret():

    try:
        # secret_name = "fnaaraniSecrets_PolyBot"
        secret_name = "polybotSecretsMQ"
        region_name='us-east-1'

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        # Attempt to retrieve the secret value
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        error_message = f"Failed to retrieve secret '{secret_name}': {e}"
        logger.error(error_message)
        return None
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logger.error(error_message)
        return None

    # Extract and return the secret value
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        logger.info(f"Retrieved secret '{secret_name}' successfully")
        return json.loads(secret)
    else:
        logger.error(f"The secret value for '{secret_name}' could not be retrieved")
        return None

secret_value = get_secret()
