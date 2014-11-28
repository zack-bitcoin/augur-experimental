"""A bunch of functions that are used by multiple threads.
"""
import pt, hashlib, re, subprocess, time, copy, networking, custom, logging, random
from json import dumps as package, loads as unpackage
from urllib import urlopen
import re
def getPublicIp():
    data = str(urlopen('http://checkip.dyndns.com/').read())
    # data = '<html><head><title>Current IP Check</title></head><body>Current IP Address: 65.96.168.198</body></html>\r\n'
    return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(data).group(1)
def add_peer(peer, current_peers=0):
    if type(peer[0]) not in [unicode, str]:
        if type(peer[0][0]) in [unicode, str]:
            peer=peer[0]
        else:
            log('not a proper peer:'+str(peer))
            return
    if current_peers==0:
        current_peers=db_get('peers_ranked')
    if peer[0] not in map(lambda x: x[0][0], current_peers):
        log('add peer: '+str(peer))
        current_peers.append([peer, 40, '0', 0])
        db_put('peers_ranked',current_peers)
def dump_out(queue):
    while not queue.empty():
        try:
            queue.get(False)
        except:
            pass
logging.basicConfig(filename=custom.log_file, level=logging.INFO)
def log(junk):
    if isinstance(junk, Exception):
        logging.exception(junk)
    else:
        logging.info(str(junk))
def can_unpack(o):
    try:
        unpackage(o)
        return True
    except:
        return False
def addr(tx): return make_address(tx['pubkeys'], len(tx['signatures']))
def sign(msg, privkey): return pt.ecdsa_sign(msg, privkey)
def verify(msg, sig, pubkey): return pt.ecdsa_verify(msg, sig, pubkey)
def privtopub(privkey): return pt.privtopub(privkey)
def hash_(x): return hashlib.sha384(x).hexdigest()[0:64]
def det_hash(x):
    """Deterministically takes sha256 of dict, list, int, or string."""
    return hash_(package(x, sort_keys=True))
def POW(block):
    #halfHash = det_hash(block)
    h=det_hash(block)
    block[u'nonce'] = random.randint(0, 10000000000000000000000000000000000000000)
    a='F'*64
    while det_hash(a) > custom.buy_shares_target:
        block[u'nonce'] += 1
        a={u'nonce': block['nonce'], u'halfHash': h}
    return block
def make_half_way(block):
    a = copy.deepcopy(block)
    a.pop('nonce')
    return({u'nonce': block['nonce'], u'halfHash': det_hash(a)})
def base58_encode(num):
    num = int(num, 16)
    alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
    base_count = len(alphabet)
    encode = ''
    if num < 0:
        return ''
    while (num >= base_count):
        mod = num % base_count
        encode = alphabet[mod] + encode
        num = num / base_count
    if num:
        encode = alphabet[num] + encode
    return encode
def make_address(pubkeys, n):
    """n is the number of pubkeys required to spend from this address."""
    return (str(len(pubkeys)) + str(n) +
            base58_encode(det_hash({str(n): pubkeys}))[0:29])
def buffer_(str_to_pad, size):
    return str_to_pad.rjust(size, '0')
def E_check(dic, key, type_):
    if not isinstance(type_, list): type_=[type_]
    if len(type_)==0: return False#to end the recursion.
    if not key in dic: return False
    if isinstance(type_[0], type):
        if not isinstance(dic[key], type_[0]): return E_check(dic, key, type_[1:])
    else:
        if not dic[key] == type_[0]: return E_check(dic, key, type_[1:])
    return True
def reveal_time_p(DB={}, n=custom.vote_reveal_length+custom.SVD_length):
    r=custom.cycle_length
    return db_get('length')%r>=(r-n)
    #return db_get('length')%20>=(20-n)
def is_number(s):
    try:
        int(s)
        return True
    except:
        return False
def kill_processes_using_ports(ports):
    popen = subprocess.Popen(['netstat', '-lpn'],
                             shell=False,
                             stdout=subprocess.PIPE)
    (data, err) = popen.communicate()
    pattern = "^tcp.*((?:{0})).* (?P<pid>[0-9]*)/.*$"
    pattern = pattern.format(')|(?:'.join(ports))
    prog = re.compile(pattern)
    for line in data.split('\n'):
        match = re.match(prog, line)
        if match:
            pid = match.group('pid')
            subprocess.Popen(['kill', '-9', pid])
def s_to_db(c): 
    response=networking.send_command(['localhost', custom.database_port], c)
    if (type(response)==dict and 'error' in response):
        time.sleep(0.001)
        log('s to db failed at '+str(c))
        return s_to_db(c)
    else:
        return response
default_entry={'count': 0, 'amount': 0, 'votecoin':{}, 'votes':{}, 'shares':{}}
def db_get(n, DB={}): return s_to_db({'type':'get', 'args':[str(n)]})
def db_put(key, dic, DB={}): return s_to_db({'type':'put', 'args':[str(key), dic]})
def db_delete(key, DB={}): return s_to_db({'type':'delete', 'args':[str(key)]})#db_put(key, 'undefined', DB)
def db_existence(key, DB={}): return s_to_db({'type':'existence', 'args':[str(key)]})
def count(address, DB):
    # Returns the number of transactions that pubkey has broadcast.
    def zeroth_confirmation_txs(address, DB):
        def is_zero_conf(t):
            other_address=make_address(t['pubkeys'], len(t['signatures']))
            return address == other_address
        return len(filter(is_zero_conf, db_get('txs')))
    current = db_get(address, DB)['count']
    zeroth=zeroth_confirmation_txs(address, DB)
    return current+zeroth
def fork_check(newblocks, DB, length, block):
    recent_hash = det_hash(block)
    their_hashes = map(lambda x: x['prevHash'] if x['length']>0 else 0, newblocks)+[det_hash(newblocks[-1])]
    b=(recent_hash not in their_hashes) and length>newblocks[0]['length']-1 and length<newblocks[-1]['length']
    return b
if __name__ == "__main__":
    a=POW({'a':'b'})
    print(a)
    print(det_hash(make_half_way(a))<custom.buy_shares_target)
    '''
    time_0=time.time()
    for i in range(100):
        timea=time.time()
        POW({'empty':0})
        print(time.time()-timea)
    print(time.time()-time_0)
    '''

