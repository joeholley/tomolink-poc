# python3
# actions.py
import logging
import os
import sys
import time
import traceback

from pylogrus import PyLogrus, JsonFormatter, TextFormatter

from google.cloud import firestore

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

def create_player(uuids):
    ref = root_collection.document(uuid)
    rels_config = os.environ.get("TL_RELATIONSHIPS")
    if rels_config:
        relationships = rels_config.split(",")
    else:
        relationships = ["friend", "other"]
    for relationship in relationships:
        pass

    #ref.set({
    #    u'capital': True
    #}, merge=True)
    return

def validate_args(args):
    # TODO(joeholley): in final, we'll need input validation to avoid malicous actors
    out_args = dict()
    out_args['direction'] = args['direction'].lower()
    out_args['relationship'] = args['relationship'].lower()
    out_args['delta'] = int(args['delta'])
    out_args['uuids'] = list(args['uuids'])

    log.withFields({'direction': out_args['direction'],
                    'relationship': out_args['relationship'],
                    'delta': out_args['delta'],
                    'uuids': out_args['uuids']}).debug("Printing request fields")

    # bail out if it is not a supported direction
    if out_args['direction'] not in ['uni', 'bi']:
        log.withFields({'direction': out_args['direction']}).error("direction is not recognized!")
        raise "relationship direction %s not recognized" % out_args['direction']

    return out_args
    
def delete_relationship(a):
    log.debug("point1")
    args = validate_args(a)

    try:
        if args['direction'] == 'bi':
          log.debug("bi-directional relationship delete")
          batch = db.batch()
          for uuid_src in args['uuids']:
            for uuid_trgt in args['uuids']:
              if uuid_src != uuid_trgt:
                # You can make updates using dot-notation for json nested keys
                # Delete will not delete the relationship dict, which is fine.
                key = "%s.%s" % (args['relationship'], uuid_trgt)
                batch.update(root_collection.document(uuid_src), {key: firestore.DELETE_FIELD})
          batch.commit()
        else:
          log.debug("uni-directional relationship delete")
          key = "%s.%s" % (args['relationship'], args['uuids'][1])
          root_collection.document(args['uuids'][0]).update({key: firestore.DELETE_FIELD})
    except Exception:
        raise

    return ""

def update_relationship(a):
    log.debug("point1")
    args = validate_args(a)
    
    try:
        if args['direction'] == 'bi':
          log.debug("bi-directional relationship update")
          batch = db.batch()
          for uuid_src in args['uuids']:
            for uuid_trgt in args['uuids']:
              if uuid_src != uuid_trgt:
                # You can make updates using dot-notation for json nested keys,
                # it's simpler than generating an entire dict like we have to
                # on create.
                key = "%s.%s" % (args['relationship'], uuid_trgt)
                batch.update(root_collection.document(uuid_src), {key: firestore.Increment(args['delta'])})
          batch.commit()
        else:
          log.debug("uni-directional relationship update")
          key = "%s.%s" % (args['relationship'], args['uuids'][1])
          root_collection.document(args['uuids'][0]).update({key: firestore.Increment(args['delta'])})
    except Exception:
        raise

    return ""

def create_relationship(a):
  log.debug("point1")
  # normalize & validate args
  args = validate_args(a)

  try:
    score = init_score()
    newdata = dict()
    if args['direction'] == 'bi':
      log.debug("bi-directional relationship create")
      batch = db.batch()
      for uuid_src in args['uuids']:
        for uuid_trgt in args['uuids']:
          if uuid_src != uuid_trgt:
            # Tried to do this using dot notation and ended up with a dot in the key name.
            newdata[args['relationship']] = dict()
            newdata[args['relationship']][uuid_trgt] = score+args['delta']
            batch.set(root_collection.document(uuid_src), newdata, merge=True) 
      batch.commit()
    else:
      log.debug("uni-directional relationship create")
      newdata[args['relationship']] = dict()
      newdata[args['relationship']][args['uuids'][1]] = score+args['delta']
      root_collection.document(args['uuids'][0]).set(newdata, merge=True) 

    log.debug("point-1")
    return {"success": True}
  except Exception as e:
    print("An Error Occured:", traceback.format_exc())
    return None 

def retrieve_player(a):
    log.debug("retrieving player")
    args = validate_args(a)

    try:
        return root_collection.document(args['uuids'][0]).get().to_dict()
    except Exception:
        print("An Error Occured:", traceback.format_exc())
        return None

def retrieve_relationship(a):
    args = validate_args(a)
    log.debug("retrieving all of relationship %s for player" % args['relationship'])

    try:
        return root_collection.document(args['uuids'][0]).get({args['relationship']}).to_dict()[args['relationship']]
    except Exception:
        print("An Error Occured:", traceback.format_exc())
        return None

def retrieve_score(a):
    args = validate_args(a)
    log.debug("retrieving score of relationship")

    try:
        key = "%s.%s" % (args['relationship'], args['uuids'][1])
        return root_collection.document(args['uuids'][0]).get({key}).to_dict()[args['relationship']][args['uuids'][1]]
    except Exception:
        print("An Error Occured:", traceback.format_exc())
        return None

def init_score():
  score_type = os.environ.get("SCORE_TYPE")
  if score_type and score_type.lower() in ['time']:
    return int(time.time())
  else:
    return 0

if __name__ == '__main__':
    print(sys.argv)
    args = {'func': sys.argv[1],
            'direction': sys.argv[2],
            'relationship': sys.argv[3],
            'delta': int(sys.argv[4]),
            'uuids': sys.argv[5:]} 
    print(args)

    if 'c' in args['func'].lower():
        print(create_relationship(args))
    if 'u' in args['func'].lower():
        print(update_relationship(args))
    if 'd' in args['func'].lower():
        print(delete_relationship(args))
    if 'r' in args['func'].lower():
        print(retrieve_player(args))
    if 'e' in args['func'].lower():
        print(retrieve_relationship(args))
    if 's' in args['func'].lower():
        print(retrieve_score(args))

