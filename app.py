import json
import requests 
from flask import Flask,jsonify
from pymongo import MongoClient
from decouple import config
from bson import ObjectId,json_util
import pprint

app = Flask(__name__)
sentence_url = "http://sentenceapi2.servers.nferx.com:8015/tagrecorder/v3/projects/"

# DB connection 
mongo_uri = config('MONGO_URI')
client = MongoClient(mongo_uri)
database = client['utkarshgrover']

@app.route('/preprocess/<id>', methods=["GET"])
def preprocess(id):
    try:
        r = requests.get(sentence_url+id, timeout=5)
    except:
        return "error reaching sentence api"

    data = r.json()
    if( data['success'] == False ):
        return 'bad project id'
    else:
        if database['projects'].find_one({"_id":ObjectId(data['result']['project']['_id'])}):
            return "project already processed"
        
        response = " "

        #process the JSON 
        models = data['result']['project']['models']
        models_result = database['models'].insert_many(models)
        #models_ids = models_result.inserted_ids
        response += "Added models to the databse with IDs " + " ".join(map(str,models_result.inserted_ids)) + "\n\n"
        #print(models_ids)

        datasets = data['result']['project']["associated_datasets"]
        dataset_id = []
        for docs in datasets:
            #no clue if duplicate datasets exists so try/except 
            if database['datasets'].find_one({"_id" : ObjectId(docs["_id"])}):
                # try :
                #     existing_doc = database['datasets'].find_one({"_id" : ObjectId(docs["_id"])})
                #     models_new = existing_doc["models_trained"]
                #     models_new.append(models)
                #     models_new = list(set(models_new))
                #     database["datasets"].find_one_and_update({"_id" : ObjectId(docs["_id"])}, {"$set": {"models_trained" : models_new}})
                # except:
                #     return "failed at modifying datasets"
                continue
            else:
                docs['_id'] = ObjectId(docs['_id'])
                #docs['models_trained'] = models
                status = database['datasets'].insert_one(docs)
                #print(status)
                dataset_id.append(status.inserted_id)

        response += "Added dataset to the databse with IDs " + " ".join(map(str,dataset_id)) + "\n\n"
        
    
        project = {}
        project['_id'] =  ObjectId(data['result']['project']['_id']) 
        project['datasets'] = datasets
        project['models'] = models
        project_insert = database['projects'].insert_one(project)

        response += "Project to the databse with ID " + str(project_insert.inserted_id) + "\n\n"
        
        return response

@app.route('/model/<id>', methods=["GET"])
def get_model(id):
    try:
        doc = database['models'].find_one({"_id": ObjectId(id)})
    except:
        return "not a valid id"

    if doc :
        return json.loads(json_util.dumps(doc)) 
    else:
        return "the model does not exists"

@app.route('/dataset/<id>', methods=["GET"])
def get_dataset(id):
    try:
        doc = database['datasets'].find_one({"_id": ObjectId(id)})
    except:
        return "not a valid id"

    if doc :
        return json.loads(json_util.dumps(doc)) 
    else:
        return "the dataset does not exists"

@app.route('/project/<id>', methods=["GET"])
def get_project(id):
    try:
        doc = database['projects'].find_one({"_id": ObjectId(id)})
    except:
        return "not a valid id"

    if doc :
        return json.loads(json_util.dumps(doc)) 
    else:
        return "the dataset does not exists"

@app.route('/trained_models/<id>', methods=["GET"])
def trained_models(id):
    try:
        docs = database['models'].find({"datasets_used.dataset_id":id})
    except:
        return "not a valid id"

    if docs :
        return jsonify({"models" : json.loads(json_util.dumps(docs))})
    else:
        return "the dataset does not exists"



if __name__ == '__main __':
    app.run(host='0.0.0.0', port=5000)