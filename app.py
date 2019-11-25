# python3
# app.py

# Required imports
import logging
import os

from flask import Flask, request, jsonify
from pylogrus import PyLogrus, JsonFormatter, TextFormatter

from google.cloud import firestore

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
db = firestore.Client()
fs = db.collection('tomos')

def get_logger():
    # POC is using a python port of the Golang logging library the final
    # version will use (when coded in golang).  It's a bit un-pythonic but will
    # ease the move from PoC to final code.
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

    # Uncomment below to output structured logs in commandline-friendly text format
    #formatter = TextFormatter(datefmt='Z', colorize=False)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

log = get_logger()
log.debug("PyLogrus initialized for structured logging")

@app.route('/users/<string:uuid_src>', methods=['GET'])
@app.route('/users/<string:uuid_src>/<string:relationship>', methods=['GET'])
@app.route('/users/<string:uuid_src>/<string:relationship>/<string=uuid_trgt>', methods=['GET'])
def retrieve_relationships(uuid_src, relationship=None, uuid_trgt=None):
    """
        retrieve_relationships() : get relationships for a user.
        - use only source uuid to get all relationships
        - use source uuid and relationship type to get all relationships of that type
        - use source & target uuids and relationship type to get that specific score 
    """
    try:
        rs_logger = log.withFields({
            'uuid_src':     uuid_src, 
            'uuid_trgt':    uuid_trgt, 
            'relationship': relationship, 
            })
        rs_logger.debug("retrieveRelationships called")

        if uuid_trgt and relationship:
            # Get requested relationship
            key = "%s.%s" % (request.json['relationship'], request.json['uuids'][1])
            relationship = fs.document(uuid_src).get({key}).to_dict()
            return jsonify({
                "success": True,
                "results": relationship[relationship][uuid_trgt],
                }), 200
        elif relationship:
            # Get all relationships of requested type
            return jsonify({
                "success": True,
                "results": fs.document(uuid_src).get({relationship}).to_dict()
                }), 200
        else:
            # Get all relationships
            return jsonify({
                "success": True, 
                "results": fs.document(uuid_src).get().to_dict()
                }) , 200

    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/updateRelationship', methods=['POST', 'PUT'])
def update_relationship():
    """
        update_relationship() : increment/decrement relationship score between users.
        - Input JSON should include: 
          - string for direction "uni" (src->trgt) or "bi" for both 
          - string for relationship type
          - array of UUID strings. First UUID in the array is always the src, second is always trgt (for POC)
          - int for how much to change the score (delta)
        Note:   This is currently implemented somewhat oddly during PoC while we decide
                if we want to be able to update more than two relationships at once.
        TODO (joeholley): Decrementing below init_score should be floored at
                          init_score (or deleted)

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
            # This is using a loop as it /could/ be easily made to modify more
            # than two players simultaneously.  Not settled on having this
            # feature yet but could see it as useful in many group-based games.
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
        - Input JSON should include: 
          - string for direction "uni" (src->trgt) or "bi" for both 
          - string for relationship type
          - array of UUID strings. First UUID in the array is always the src, second is always trgt (for POC)
    """

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

@app.route('/createRelationship', methods=['POST', 'PUT'])
def create_relationship():
    """
        create_relationship() : create relationship with initial score between users.
        - Input JSON should include: 
          - string for direction "uni" (src->trgt) or "bi" for both 
          - string for relationship type
          - array of UUID strings. First UUID in the array is always the src, second is always trgt (for POC)
          - int for how much to change the initial score (delta)
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

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
  app.run(threaded=True, host='0.0.0.0', port=port)
