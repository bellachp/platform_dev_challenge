from devchallenge.mock_api import Mock_Prescription

import mongomock


def test_get_prescription_doc():

    # instantiate mock mongo
    client = mongomock.MongoClient()

    resource = Mock_Prescription()
    doc = resource.get(1, client)

    assert doc is not None


def test_post_pescription_doc():

    # instantiate mock mongo
    client = mongomock.MongoClient()
    
    resource = Mock_Prescription()

    # create mock prescrip obj
    prescrip_obj = {}
    prescrip_obj["model_target"] = "mock targ"
    prescrip_obj["model_outcome"] = "mock outcome"
    prescrip_obj["target_objectives"] = [{}]

    prescrip_doc = {}
    prescrip_doc["prescription"] = prescrip_obj

    doc = resource.post(1, prescrip_doc, client)
    print(doc)

    assert doc is not None

