import logging
import os

from flask import Flask, abort, jsonify, request
from flask_restful import Api, Resource
# from pymongo import DESCENDING

from devchallenge import mongo_helpers, schemas, prediction_api

logger = logging.getLogger(__name__)

mongo_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/test_db')


class Mock_Prescription():
    def get(self, case_id, mongo_client):
        """
        Get the latest prescription for a given case

        Returns mongo document as json
        ---
        tags:
          - prescription
        parameters:
          - in: path
            name: case_id
            description: Case ID
            required: true
            type: integer
            x-example: 1
        responses:
            200:
                description: OK
            400:
                description: Bad Request - invalid request params
            401:
                description: Unauthorized - user does not have permission to view prescription
            404:
                description: No prescription found
            503:
                description: Service Unavailable - connection to the database failed
        """
        case_id = int(case_id)

        db = mongo_client.get_database()

        prescription_cursor = mongo_helpers.retreive_doc(
            db.prescription,
            {"case_id": case_id},
            find_one=False,
            # sort_params=("timestamp", DESCENDING),
        )
        prescriptions = list(prescription_cursor)
        if len(prescriptions) == 0:
            logger.warning("no prescriptions found for case")
            abort(404, "No prescription found")

        most_recent_prescription = prescriptions[0]
        logger.info("prescription found")

        return jsonify(most_recent_prescription)

    def post(self, case_id, data_json, mongo_client):
        """
        Submit a prescription for predictions

        Inserts raw JSON object and returns full prescription object
        ---
        tags:
          - prescription
        parameters:
          - in: path
            name: case_id
            description: Case ID
            required: true
            type: integer
            x-example: 1
          - in: body
            name: prescription
            description: new prescription
            required: true
            schema:
                $ref: '#/definitions/Prescription'
        responses:
            200:
                description: OK
                schema:
                    type: object
                    properties:
                        prescription_id:
                            type: string
                        predictions:
                            $ref: '#/definitions/RiskPrediction'
            400:
                description: Bad Request - invalid request params
            401:
                description: Unauthorized - user does not have permission to create plans
            500:
                description: Internal Server Error - analytics service failed
            503:
                description: Service Unavailable - connection to the database failed
        """
        case_id = int(case_id)
        args = data_json

        db = mongo_client.get_database()

        logger.info("request received", extra={"request_data": args})

        prescription_doc = args.get(schemas.PRESCRIPTION_FIELD)

        # save prescription doc
        prescription_doc = mongo_helpers.add_user_metadata(
            prescription_doc, request.headers.get("Username")
        )
        prescription_doc["case_id"] = case_id

        prescription_docid, success = mongo_helpers.persist_doc(db.prescription, prescription_doc)

        prescription_doc["_id"] = prescription_docid
        logger.info('prescription saved', extra={"doc_id": prescription_docid})

        # retrieve associated case doc
        case_query = {"_id": case_id}
        case_doc = mongo_helpers.retrieve_doc(db.cases, case_query)
        prescription_doc["case"] = case_doc

        prediction_resp = prediction_api.get_risk_prediction(url="mock_url", body=prescription_doc)

        # store prediction
        this_prediction = prediction_resp.json()
        prediction_docid, success = mongo_helpers.persist_doc(db.predictions, this_prediction)

        post_resp = {"prescription_id": prescription_docid, 
                     "prediction_id": prediction_docid,
                     "prediction": this_prediction}
        return post_resp


