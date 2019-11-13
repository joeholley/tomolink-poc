# python3
# app.py

# Required imports
import logging
import os
import traceback

from flask import Flask, request, jsonify
from pylogrus import PyLogrus, JsonFormatter, TextFormatter

from google.cloud import firestore

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
# cred = credentials.Certificate('key.json')
# default_app = initialize_app(cred)
db = firestore.Client()
root_collection = db.collection('tomos')

def get_logger():
    logging.setLoggerClass(PyLogrus)

    logger = logging.getLogger(__name__)  # type: PyLogrus
    logger.setLevel(logging.DEBUG)

    enabled_fields = [
        ('name', 'logger_name'),
        ('asctime', 'service_timestamp'),
        ('levelname', 'level'),
        ('threadName', 'thread_name'),
        'message',
        ('exception', 'exception_class'),
        ('stacktrace', 'stack_trace'),
        'module',
        ('funcName', 'function')
    ]

    formatter = JsonFormatter(datefmt='Z', enabled_fields=enabled_fields, indent=2, sort_keys=True)

    formatter = TextFormatter(datefmt='Z', colorize=False)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

log = get_logger()
log.debug("PyLogrus initialized for structured logging")

@app.route('/add', methods=['POST'])
def create():
  """
    create() : Add document to Firestore collection with request body.
    Ensure you pass a custom ID as part of json body in post request,
    e.g. json={'id': '1', 'title': 'Write a blog post'}
  """
  try:
    uid = request.json['id']
    root_collection.document(uid).set(request.json)
    return jsonify({"success": True}), 200
  except Exception as e:
    return f"An Error Occured: {e}"

@app.route('/test', methods=['POST'])
def test():
  try:
    uid = request.json['id']
    contents = request.get_json()
    contents.pop('id', None)
    root_collection.document(uid).set(contents)
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
      tomo = root_collection.document(tomo_id).get()
      return jsonify(tomo.to_dict()), 200
    else:
      all_tomos = [doc.to_dict() for doc in root_collection.stream()]
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
    uid = request.json['id']
    root_collection.document(uid).update(request.json)
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
    root_collection.document(tomo_id).delete()
    return jsonify({"success": True}), 200
  except Exception as e:
    return f"An Error Occured: {e}"

@app.route('/createRelationship', methods=['POST', 'PUT'])
def create_relationship():
  """
    create_relationship() : create document in Firestore collection with request body.
    This OVERWRITES if the relationship already exists.
    Ensure you pass a custom ID as part of json body in post request,
    e.g. json={'id': '1', 'title': 'Write a blog post today'}
  """
  try:
    log.debug("point1")

    # TODO(joeholley): in final, we'll need input validation to avoid malicous actors
    direction = request.json['direction'].lower()
    relationship = request.json['relationship'].lower()
    delta = int(request.json['delta'])
    uuids = list(request.json['uuids'])

    log.withFields({'direction': direction,
                    'relationship': relationship,
                    'delta': delta,
                    'uuids': uuids}).debug("Printing request fields")

    # bail out if it is not a supported direction
    if direction not in ['uni', 'bi']:
        log.withFields({'direction': request.json['direction']}).error("direction is not recognized!")
        raise "relationship direction %s not recognized" % request.json['direction']

    doc_refs = []
    if direction == 'bi':
      for uuid_src in uuids:
        for uuid_trgt in uuids:
          if uuid_src != uuid_trgt:
            doc_refs.append(root_collection.document(uuid_src).collection(relationship).document(uuid_trgt))
    else:
      doc_refs.append(root_collection.document(uuids[0]).collection(relationship).document(uuids[1]))

    log.debug("point2")
    transaction = db.transaction()

    @firestore.transactional
    def update_in_transaction(transaction, doc_refs, delta):
      new_scores = []
      log.debug("point4")
      for doc_ref in doc_refs:
        new_scores.append(doc_ref.get(transaction=transaction).get(u'score') + delta)
      log.debug("point5")
      for i in range(0, len(doc_refs)):
        transaction.update(doc_refs[i], {u'score': new_scores[i]})
      log.debug("point6")

    log.debug("point3")
    update_in_transaction(transaction, doc_refs, delta)

    log.debug("point-2")
    result = transaction.commit()
    log.debug("point-1")
    return jsonify({"success": True, "result": result}), 200
#    return jsonify({"success": True}), 200
  except Exception as e:
    return f"An Error Occured: {e}", traceback.format_exc()

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
  app.run(threaded=True, host='0.0.0.0', port=port)
