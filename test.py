import boto3
from PIL import Image
client = boto3.client('s3')
response = client.get_object(
    Bucket='mqbucket1',
    Key='poster_iron.jpeg'
)
binary_image = response['Body']
opend = Image.open(binary_image)
opend.save("iron.jpeg")