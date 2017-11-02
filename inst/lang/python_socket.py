#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import socket
import contextlib
import traceback
import sys
import re
from io import BytesIO


# Compatibility shim for Py2/3
PY2 = sys.version_info[0] == 2

if not PY2:
    # execfile definition is from `future` package: see
    # http://python-future.org
    def execfile(filename, myglobals=None, mylocals=None):
        """
        Read and execute a Python script from a file in the given namespaces.
        The globals and locals are dictionaries, defaulting to the current
        globals and locals. If only globals is given, locals defaults to it.
        """
        if myglobals is None:
            # There seems to be no alternative to frame hacking here.
            caller_frame = inspect.stack()[1]
            myglobals = caller_frame[0].f_globals
            mylocals = caller_frame[0].f_locals
        elif mylocals is None:
            # Only if myglobals is given do we set mylocals to it.
            mylocals = myglobals
        if not isinstance(myglobals, Mapping):
            raise TypeError('globals must be a mapping')
        if not isinstance(mylocals, Mapping):
            raise TypeError('locals must be a mapping')
        with open(filename, "rbU") as fin:
             source = fin.read()
        code = compile(source, filename, "exec")
        exec_(code, myglobals, mylocals)



script, PORT, token_file, sep = sys.argv

##### set up a server
HOST = 'localhost'
PORT = int(PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket created
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# the SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
# without waiting for its natural timeout to expire.
# see: https://docs.python.org/2/library/socket.html

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + '; Message: ' + msg[1])
    quit()
s.listen(10) # Socket now listening

@contextlib.contextmanager
def stdoutIO(stdout=None):
    '''
    store outputs from stdout
    '''
    old = sys.stdout
    if stdout is None:
        stdout = BytesIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

####### now keep talking with the client
while True:
    ### wait to accept a connection
    conn, addr = s.accept() # Connected with  + addr[0] + str(addr[1])
    input_data = conn.recv(1024000)
    try:
        input_decoded = input_data.encode('ascii')
        if re.sub('\s', '', input_decoded) == 'quit()':
            break
    except:
        pass
    ### write the codes into a file
    with open(token_file, 'wb') as f:
        f.write(input_data)
    ### print codes; execute codes
    with stdoutIO() as output:
        print(input_data)
        print(sep)
        try:
            execfile(token_file)
        except:
            traceback.print_exc()
    ### send output
    output_data = output.getvalue()
    conn.send(output_data)
    conn.close()
###### close & quit
conn.close()
s.shutdown(2)
s.close()
