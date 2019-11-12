# app.py

# Required imports
import os
from flask import Flask, request, jsonify
#from firebase_admin import credentials, firestore, initialize_app
from google.cloud import firestore


# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
# cred = credentials.Certificate('key.json')
# default_app = initialize_app(cred)
db = firestore.Client()
tomo_ref = db.collection('tomos')

@app.route('/add', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post'}
    """
    try:
        id = request.json['id']
        tomo_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON.
        tomo : Return document that matches query ID.
        all_tomos : Return all documents.
    """
    try:
        # Check if ID was passed to URL query
        tomo_id = request.args.get('id')
        if tomo_id:
            tomo = tomo_ref.document(tomo_id).get()
            return jsonify(tomo.to_dict()), 200
        else:
            all_tomos = [doc.to_dict() for doc in tomo_ref.stream()]
            return jsonify(all_tomos), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """
    try:
        id = request.json['id']
        tomo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection.
    """
    try:
        # Check for ID in URL query
        tomo_id = request.args.get('id')
        tomo_ref.document(tomo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)
