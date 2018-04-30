from flask import Flask, jsonify, request
import vera
import threading, time, json, os
import secrets

DIRECTORY = os.path.dirname(os.path.realpath(__file__)) + '/'
PERMISSION_FILE = DIRECTORY + 'permissions.json'
app = Flask(__name__)
ve = None

def unlock():
    global ve
    if ve is None:
        ve = vera.VeraRemote(secrets.VERA_USER, secrets.VERA_PASS, secrets.VERA_ID)
    dev = ve.get_device('Entry Lock')
    print('unlocking door')
    dev.set_lock(False)
    time.sleep(10)
    print('locking door')
    dev.set_lock(True)

def add_permission(card, fn):
    permissions = {}
    with open(PERMISSION_FILE) as f:
        permissions = json.loads(f.read())
    
    if card not in permissions[fn]:
        permissions[fn].append(card)

    with open(PERMISSION_FILE, 'w') as f:
        f.write(json.dumps(permissions))

@app.route('/')
def action():
    args = request.args
    if 'fn' not in args or 'key' not in args or 'card' not in args:
        return jsonify({'status': 'FAIL', 'reason': 'Missing required argument'})

    fn = args['fn']
    key = args['key']
    card = args['card']

    if not key == secrets.SYZCARD_KEY:
        return jsonify({'status': 'FAIL', 'reason': 'Invalid key'})

    if not check_permission(fn, key, card):
        return jsonify({'status': 'FAIL', 'reason': 'User not authorized'})

    if fn == 'unlock':
        threading.Thread(target=unlock).start()
    elif fn == 'add':
        add_permission(card, args['perm_fn'])
    else:
        return jsonify({'status': 'FAIL', 'reason': 'Invalid function'})

    return jsonify({'status': 'OK'})


def check_permission(fn, key, card):
    permissions = {}
    try:
        with open(PERMISSION_FILE) as f:
            permissions = json.loads(f.read())
    except IOError:
        with open(PERMISSION_FILE, 'w') as f:
            f.write(json.dumps({}))

    if fn == 'add': return True
    if fn not in permissions: return False

    return card in permissions[fn]

if __name__ == '__main__':
    app.run(port=6660)
