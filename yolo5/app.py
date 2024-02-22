import json
import time
import boto3
import uuid
import yaml
import os
from pathlib import Path
from flask import Flask, request, jsonify
from detect import run
from loguru import logger
from mongoServerApi import mongoAPI
from bson import json_util

IMAGES_BUCKET = os.environ['BUCKET_NAME']
MONGO_USER = os.environ['MONGO_USER']
MONGO_PASS = os.environ['MONGO_PASS']
DATABASE = 'images'
COLLECTION = 'predictions'

with open("data/coco128.yaml", "rb") as stream:
    names = yaml.safe_load(stream)['names']

app = Flask(__name__)


@app.route('/predict', methods=['POST', 'GET'])
def predict():
    # Generates a UUID for this current prediction HTTP request. This id can be used as a reference in logs to identify and track individual prediction requests.
    prediction_id = str(uuid.uuid4())
    logger.info(f'prediction: {prediction_id}. start processing')
    try:
        img_name = request.args.get('imgName')
    except:
        return jsonify({"error": "No image name provided"}), 400

    try:
        bucket_name = os.getenv('BUCKET_NAME')
        s3 = boto3.client('s3')

        # create directory if it does not exist
        if not os.path.exists('Images'):
            os.mkdir('Images')

        s3.download_file(IMAGES_BUCKET, img_name,
                            f"Images/{os.path.basename(img_name)}")
        original_img_path = f"Images/{os.path.basename(img_name)}"
        logger.info(
            f'prediction: {prediction_id}/{original_img_path}. Download img completed')
    except:
        return jsonify({"error": f"Failed to download the file from S3."}), 500

    # Predicts the objects in the image
    run(
        weights='yolov5s.pt',
        data='data/coco128.yaml',
        source=original_img_path,
        project='static/data',
        name=prediction_id,
        save_txt=True
    )

    logger.info(f'prediction: {prediction_id}/{original_img_path}. done')

    # This is the path for the predicted image with labels
    # The predicted image typically includes bounding boxes drawn around the detected objects, along with class labels and possibly confidence scores.
    # had to change the predicted img path
    predicted_img_path = Path(
        f"static/data/{prediction_id}/{original_img_path.split('/')[-1]}")

    try:
        s3.upload_file(predicted_img_path, IMAGES_BUCKET,
                            f"static/{prediction_id}/{os.path.basename(predicted_img_path)}")
        logger.info(
            f'prediction: {prediction_id}/{original_img_path}. Upload img completed')
    except:
        return jsonify({"error": f"Failed to upload the file to S3."}), 500

    # Parse prediction labels and create a summary
    pred_summary_path = Path(
        f"static/data/{prediction_id}/labels/{os.path.basename(img_name).split('.')[0]}.txt")
    if pred_summary_path.exists():
        with open(pred_summary_path) as f:
            labels = f.read().splitlines()
            labels = [line.split(' ') for line in labels]
            labels = [{
                'class': names[int(l[0])],
                'cx': float(l[1]),
                'cy': float(l[2]),
                'width': float(l[3]),
                'height': float(l[4]),
            } for l in labels]

        logger.info(
            f'prediction: {prediction_id}/{original_img_path}. prediction summary:\n\n{labels}')

        prediction_summary = {
            'prediction_id': str(prediction_id),
            'original_img_path': original_img_path,
            'predicted_img_path': str(predicted_img_path),
            'labels': labels,
            'time': time.time()
        }

        try:
            data = json.loads(json_util.dumps(prediction_summary))
            conn = mongoAPI(MONGO_USER, MONGO_PASS, DATABASE, COLLECTION)
            conn.insert_prediction(data)
        except:
            logger.warning("Error while saving prediction info into MongoDB.")

        return prediction_summary
    else:
        return f'prediction: {prediction_id}/{original_img_path}. prediction result not found', 404


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=4000)
