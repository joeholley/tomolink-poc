# python3
# app.py

# Required imports
import logging
import os
import time
import traceback

from flask import Flask, request, jsonify
from pylogrus import PyLogrus, JsonFormatter, TextFormatter

from google.cloud import firestore

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
db = firestore.Client()
fs = db.collection('tomos')

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

    formatter = JsonFormatter(datefmt='Z', enabled_fields=enabled_fields, sort_keys=True)

    #formatter = TextFormatter(datefmt='Z', colorize=False)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

log = get_logger()
log.debug("PyLogrus initialized for structured logging")

#@app.route('/add', methods=['POST'])
#def create():
#  """
#    create() : Add document to Firestore collection with request body.
#    Ensure you pass a custom ID as part of json body in post request,
#    e.g. json={'id': '1', 'title': 'Write a blog post'}
#  """
#  try:
#    uid = request.json['id']
#    fs.document(uid).set(request.json)
#    return jsonify({"success": True}), 200
#  except Exception as e:
#    return f"An Error Occured: {e}"

#@app.route('/test', methods=['POST'])
#def test():
#  try:
#    uid = request.json['id']
#    contents = request.get_json()
#    contents.pop('id', None)
#    fs.document(uid).set(contents)
#    return jsonify({"success": True}), 200
#  except Exception as e:
#    return f"An Error Occured: {e}"

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
      tomo = fs.document(tomo_id).get()
      return jsonify(tomo.to_dict()), 200
    else:
      all_tomos = [doc.to_dict() for doc in fs.stream()]
      return jsonify(all_tomos), 200
  except Exception as e:
    return f"An Error Occured: {e}"

@app.route('/users/<string:uuid>/<string:relationship>', methods=['GET'])
def retrieve_relationships(uuid, relationship):
    """
        retrieve_relationships() : get relationships for a user.
        pass only uuid to get all relationships
        NYI pass uuid and relationship type to get all relationships of that type
    """
    try:
        rs_logger = log.withFields({
            'uuid': uuid, 
            'relationship': relationship, 
            })
        rs_logger.debug("retrieveRelationships called")

        if request.args.get('relationship'):
             Get requested relationship
            return jsonify({
                "success": True,
                "results": fs.document(uuid).get(relationship).to_dict()
                }), 200
        else:
        #if True:
            # Get all relationships
            return jsonify({
                "success": True, 
                "results": fs.document(uuid).get().to_dict()
                }) , 200

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/retrieveRelationship', methods=['POST', 'PUT'])
def retrieve_relationship():
    """
        retrieve_relationship() : get one relationship score between source and target users. 
    """
    try:
        rr_logger = log.withFields({
            'relationship': request.json['relationship'],
            'uuid_src':     request.json['uuids'][0],
            'uuid_trgt':    request.json['uuids'][1],
            })
        rr_logger.debug("retrieveRelationship called")
        key = "%s.%s" % (request.json['relationship'], request.json['uuids'][1])
        relationship = fs.document(request.json['uuids'][0]).get({key}).to_dict()

        return jsonify({"success": True, 
                        "results": relationship[request.json['relationship']][request.json['uuids'][1]]}), 200

    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/retrievePlayer', methods=['GET'])
def retrieve_player():
    """
        retrieve_player() : get all relationships for a user.
    """
    try:
        rp_logger = log.withFields({'uuid': request.args.get('uuid')})
        rp_logger.debug("retrievePlayer called")
        player = fs.document(request.args.get('uuid')).get().to_dict()

        return jsonify({"success": True, "results": player}), 200

    except Exception as e:
        return f"An Error Occured: {e}"


@app.route('/updateRelationship', methods=['POST', 'PUT'])
def update_relationship():
    """
        update_relationship() : increment/decrement relationship score between users.
        TODO (joeholley): Decrementing below init_score should be floored at init_score (or deleted)
    """
    try:
        ur_logger = log.withFields({
            'direction':    request.json['direction'],
            'relationship': request.json['relationship'],
            'uuid_src':     request.json['uuids'][0],
            'uuid_trgt':    request.json['uuids'][1],
            'delta':        request.json['delta'],
            })
        ur_logger.debug("updateRelationship called")

	# TODO(joeholley): configurable initial score
        if request.json['direction'] == 'bi':
            ur_logger.debug("bi-directional relationship update")
            batch = db.batch()
            for uuid_src in request.json['uuids']:
                for uuid_trgt in request.json['uuids']:
                    if uuid_src != uuid_trgt:
                        # Nested JSON keys are handled using dot operators in firestore
                        key = "%s.%s" % (request.json['relationship'], uuid_trgt)
                        batch.update(fs.document(uuid_src), {key: firestore.Increment(int(request.json['delta']))})
            batch.commit()
        else:
            ur_logger.debug("uni-directional relationship update")
            key = "%s.%s" % (request.json['relationship'], request.json['uuids'][1])
            fs.document(request.json['uuids'][0]).update({key: firestore.Increment(int(request.json['delta']))})

        return jsonify({"success": True}), 200

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/deleteRelationship', methods=['GET', 'DELETE'])
def delete_relationship():
    """
      delete_relationship() : Delete the relationship between two users.
    """
    # TODO(joeholley): final will require input validation

    try:
        dr_logger = log.withFields({
            'direction':    request.json['direction'],
            'relationship': request.json['relationship'],
            'uuid_src':     request.json['uuids'][0],
            'uuid_trgt':    request.json['uuids'][1],
            })
        dr_logger.debug("deleteRelationship called")

        if request.json['direction'] == 'bi':
            dr_logger.info("bi-directional relationship delete")
            batch = db.batch()
            for uuid_src in request.json['uuids']:
                for uuid_trgt in request.json['uuids']:
                    if uuid_src != uuid_trgt:
                        # Nested JSON keys are handled using dot operators in firestore
                        # Delete will not delete the relationship dict, which is fine.
                        key = "%s.%s" % (request.json['relationship'], uuid_trgt)
                        batch.update(fs.document(uuid_src), {key: firestore.DELETE_FIELD})
            batch.commit()
        elif request.json['direction'] == 'uni':
            dr_logger.info("uni-directional relationship delete")
            # Nested JSON keys are handled using dot operators in firestore
            key = "%s.%s" % (request.json['relationship'], request.json['uuids'][1])
            fs.document(request.json['uuids'][0]).update({key: firestore.DELETE_FIELD})

        return jsonify({"success": True}), 200

    except Exception as e:
        return f"An Error Occured: {e}"


  #try:
  #  # Check for ID in URL query
  #  tomo_id = request.args.get('id')
  #  fs.document(tomo_id).delete()
  #  return jsonify({"success": True}), 200
  #except Exception as e:
  #  return f"An Error Occured: {e}"

@app.route('/createRelationship', methods=['POST', 'PUT'])
def create_relationship():
    """
        create_relationship() : create relationship with initial score between users.
    """
    try:
        cr_logger = log.withFields({
            'direction':    request.json['direction'],
            'relationship': request.json['relationship'],
            'uuid_src':     request.json['uuids'][0],
            'uuid_trgt':    request.json['uuids'][1],
            'delta':        request.json['delta'],
            })
        cr_logger.debug("createRelationship called")

	# TODO(joeholley): configurable initial score
        score = 0 
        newdata = dict()
        if request.json['direction'] == 'bi':
            cr_logger.debug("bi-directional relationship create")
            batch = db.batch()
            for uuid_src in request.json['uuids']:
                for uuid_trgt in request.json['uuids']:
                    if uuid_src != uuid_trgt:
                        # Tried to do this using dot notation and ended up with a dot in the key name.
			# Turns out dot notation only works on existing nexted JSON.
                        newdata[request.json['relationship']] = dict()
                        newdata[request.json['relationship']][uuid_trgt] = score+int(request.json['delta'])
                        batch.set(fs.document(uuid_src), newdata, merge=True)
            batch.commit()
        else:
            cr_logger.debug("uni-directional relationship create")
            newdata[request.json['relationship']] = dict()
            newdata[request.json['relationship']][request.json['uuids'][1]] = score+int(request.json['delta'])
            fs.document(request.json['uuids'][0]).set(newdata, merge=True)

        return jsonify({"success": True}), 200

    except Exception as e:
        return f"An Error Occured: {e}"

#  try:
#    log.debug("point1")
#
#    # TODO(joeholley): in final, we'll need input validation to avoid malicous actors
#    direction = request.json['direction'].lower()
#    relationship = request.json['relationship'].lower()
#    delta = int(request.json['delta'])
#    uuids = list(request.json['uuids'])
#
#    log.withFields({'direction': direction,
#                    'relationship': relationship,
#                    'delta': delta,
#                    'uuids': uuids}).debug("Printing request fields")
#
#    # bail out if it is not a supported direction
#    if direction not in ['uni', 'bi']:
#        log.withFields({'direction': request.json['direction']}).error("direction is not recognized!")
#        raise "relationship direction %s not recognized" % request.json['direction']
#
#    doc_refs = []
#    if direction == 'bi':
#      for uuid_src in uuids:
#        for uuid_trgt in uuids:
#          if uuid_src != uuid_trgt:
#            doc_refs.append(fs.document(uuid_src).collection(relationship).document(uuid_trgt))
#    else:
#      doc_refs.append(fs.document(uuids[0]).collection(relationship).document(uuids[1]))
#
#    log.debug("point2, len(doc_refs) %s" % len(doc_refs))
#    transaction = db.transaction()
#
#    @firestore.transactional
#    def update_in_transaction(transaction, doc_refs, delta):
#      new_scores = []
#      log.debug("point4")
#      snapshot = fs.document('joja').get(transaction=transaction)
#      log.debug("point4.1, is this printable %s" % snapshot)
#      ha = snapshot.get(u'tomodachi')
#
#      log.debug("point4.2 tomodachi value %s" % ha)
#      try:
#        ha = snapshot.get(u'tomodaci')
#        log.debug("point4.3 tomodaci value %s" % ha)
#      except Exception as e:
#        log.debug("point4.3 tomodaci threw error %s" % e)
#        pass

#      for doc_ref in doc_refs:
#        log.debug("point4.1")
#        score = doc_ref.get(transaction=transaction).get(u'score')
#        try:
#          new_scores.append(doc_ref.get(transaction=transaction).get(u'score') + delta)
#        except Exception:
#          log.error(f"An Error Occured: {e}", traceback.format_exc())
#          new_scores.append(delta)
#      log.debug("point5")
#      for i in range(0, len(doc_refs)):
#        transaction.update(doc_refs[i], {u'score': new_scores[i]})
#      log.debug("point6")
#
#    log.debug("point3")
#    update_in_transaction(transaction, doc_refs, delta)
#
#    log.debug("point-2")
#    result = transaction.commit()
#    log.debug("point-1")
#    return jsonify({"success": True, "result": result}), 200
##    return jsonify({"success": True}), 200
#  except Exception as e:
#    return f"An Error Occured: {e}", traceback.format_exc()

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
  app.run(threaded=True, host='0.0.0.0', port=port)
