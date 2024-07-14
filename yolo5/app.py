import json
import time
import datetime
from pathlib import Path
import botocore
from detect import run
import uuid
import yaml
from loguru import logger
import os
import boto3
from botocore.exceptions import ClientError
from sec import secret_keys
from bson import json_util
from dynamodbAPI import dynamodbAPI

images_bucket = secret_keys["BUCKET_NAME"]
region_name = os.environ["REGION_NAME"]
queue_url = os.environ["SQS_URL"]
sns_topic_arn = os.environ["SNS_ARN"]


with open("data/coco128.yaml", "rb") as stream:
    names = yaml.safe_load(stream)["names"]

sqs_client = boto3.client("sqs", region_name=region_name)
sns_client = boto3.client("sns", region_name=region_name)


def predict():
    logger.info("Started...")
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            VisibilityTimeout=60,
            WaitTimeSeconds=20,
        )
        prediction_id = str(uuid.uuid4())

        logger.info(f"prediction: {prediction_id}. start processing")
        # Receives a URL parameter representing the image to download from S3
        if "Messages" in response:
            message = response["Messages"][0]["Body"]
            receipt_handle = response["Messages"][0]["ReceiptHandle"]
            msg_id = response["Messages"][0]["MessageId"]
            logger.info(response)
            # TODO download img_name from S3, store the local image path in original_img_path
            client = boto3.client("s3", region_name=region_name)
            # create directory if it does not exist
            if not os.path.exists("Images"):
                os.mkdir("Images")
            # download image to Images folder
            message = json.loads(message)
            img_name = message["path"]
            try:
                client.download_file(
                    images_bucket, img_name, f"Images/{os.path.basename(img_name)}"
                )
            except ClientError as e:
                logger.error(e)
                continue
            original_img_path = f"Images/{os.path.basename(img_name)}"

            logger.info(
                f"prediction: {prediction_id}/{original_img_path}. Download img completed"
            )

            # Predicts the objects in the image
            run(
                weights="yolov5s.pt",
                data="data/coco128.yaml",
                source=original_img_path,
                project="static/data",
                name=prediction_id,
                save_txt=True,
            )

            logger.info(f"prediction: {prediction_id}/{original_img_path}. done")

            # This is the path for the predicted image with labels
            # The predicted image typically includes bounding boxes drawn around the detected objects, along with class labels and possibly confidence scores.
            ## had to change the predicted img path
            predicted_img_path = Path(
                f"static/data/{prediction_id}/{original_img_path.split('/')[-1]}"
            )
            # TODO Uploads the predicted image (predicted_img_path) to S3 (be careful not to override the original image).
            # This will upload the predicted images with same file structure found locally
            try:
                client.upload_file(
                    predicted_img_path,
                    images_bucket,
                    f"static/{prediction_id}/{os.path.basename(predicted_img_path)}",
                )
            except ClientError as e:
                logger.error(e)
                continue
            # Parse prediction labels and create a summary
            pred_summary_path = Path(
                f"static/data/{prediction_id}/labels/{os.path.basename(img_name).split('.')[0]}.txt"
            )
            if pred_summary_path.exists():
                with open(pred_summary_path) as f:
                    labels = f.read().splitlines()
                    labels = [line.split(" ") for line in labels]
                    labels = [
                        {
                            "class": names[int(l[0])],
                            "cx": float(l[1]),
                            "cy": float(l[2]),
                            "width": float(l[3]),
                            "height": float(l[4]),
                        }
                        for l in labels
                    ]

                logger.info(
                    f"prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}"
                )

                prediction_summary = {
                    "prediction_id": prediction_id,
                    "original_img_path": original_img_path,
                    "predicted_img_path": f"{predicted_img_path}",
                    "labels": labels,
                    "time": time.time(),
                }

                try:
                    # Get the current time in epoch format
                    current_epoch = int(datetime.datetime.now().timestamp())
                    # Add 5 minutes to the current time
                    new_epoch = current_epoch + (5 * 60)  # 1 minutes in seconds
                    Item = {
                        "_id": {"S": msg_id},
                        "TTL": {"N": str(new_epoch)},
                        "text": {"S": json.dumps(prediction_summary)},
                    }
                    # Upload prediction_summary to dynamodb
                    dynamo_obj = dynamodbAPI()
                    response = dynamo_obj.put_item(Item=Item)
                except botocore.exceptions as e:
                    logger.error(e)
                    continue

                # Send sns to Telegrambot
                result = {
                    "job_id": msg_id,
                    "chat_id": message["chat_id"],
                    "msg_id": message["msg_id"],
                    "Status_Code": 200,
                }
                try:
                    response = sns_client.publish(
                        TopicArn=sns_topic_arn,
                        Message=json.dumps({"default": json.dumps(result)}),
                        MessageStructure="json",
                    )
                    if response["MessageId"]:
                        # Delete message from Queue
                        sqs_client.delete_message(
                            QueueUrl=queue_url, ReceiptHandle=receipt_handle
                        )
                except botocore.exceptions as e:
                    logger.error(e)
                    continue
            else:
                result = {
                    "job_id": msg_id,
                    "chat_id": message["chat_id"],
                    "msg_id": message["msg_id"],
                    "Status_Code": 404,
                }
                response = sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Message=json.dumps({"default": json.dumps(result)}),
                    MessageStructure="json",
                )
                sqs_client.delete_message(
                    QueueUrl=queue_url, ReceiptHandle=receipt_handle
                )
        else:
            continue


predict()
