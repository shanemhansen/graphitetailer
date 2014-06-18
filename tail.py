#!/usr/bin/env python
"""
tail.py is a script for tailing from a log file and sending it
to graphite
"""
import re
import os
import argparse
import time
import sre_constants
import socket
import functools

def main():
    """
    main func
    """
    parser = argparse.ArgumentParser(description='Tail a log for metrics')
    parser.add_argument('regex', help='regular expression for extracting a float')
    parser.add_argument('filename', help='filename to tail')
    parser.add_argument(
	'--tsformat', default="%Y-%m-%d %H:%M:%S", help="time formatting string used in logs"
    )
    parser.add_argument('--graphite', default='localhost:2003', help='address of graphite listener')
    parser.add_argument('--key')
    args = parser.parse_args()
    if not args.key:
	print "key is required"
	return
    host, port = args.graphite.split(":")
    port = int(port)
    try:
	regex = re.compile(args.regex)
    except sre_constants.error, regexerr:
	print "Couldn't comile regex {0}, {1}".format(args.regex, regexerr)
	return
    if not os.path.exists(args.filename):
	raise Exception("can't find {}".format(args.filename))

    app = App(regex, args.filename, args.tsformat, args.key, (host, port))
    app.tail_file()

nil = None
def goify(f):
    """
    You know why
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
	"""
	Wrap wrap a function that can return an error
	in a tuple of (result, error)
	"""
	try:
	    return (f(*args, **kwargs), None)
	except Exception, e:
	    return None, e
    return wrapper

class App(object):
    """
    Appety-app
    """
    def __init__(self, regex, filename, tsformat, key, addr):
	self.regex = regex
	self.filename = filename
	self.tsformat = tsformat
	self.key = key
	self.addr = addr
	self.conn = socket.create_connection(addr)
	self.conn.settimeout(30)


    def tail_file(self):
        """
        tail a stream, reopen every once in a while
        """
	file_obj = open(self.filename)
	@goify
        def stat():
            """ return the inode"""
	    return os.stat(self.filename).st_ino
        inode = stat()
        while True:
            line, err = goify(file_obj.readline)()
            print line
	    if err != nil:
		#couldn't read line, break
		break
            if line == "":
                # look to see if inode has changed
                latest_inode, err = stat()
		if err != nil:
		    time.sleep(1)
		    continue
                if inode != latest_inode:
                    #it has, reopen the file
                    file_obj.close()
                    # also, if we just statted it, it's likely
		    # to exist (although
                    # there's a race condition)
                    file_obj, err = goify(open)(self.filename)
		    if err == nil:
			inode = latest_inode
                    continue
                time.sleep(1)
                continue
            match = self.regex.search(line)
            if match is None:
                continue

            val = float(match.group('duration').replace(",", ""))
            try:
                timestamp = time.mktime(
		    time.strptime(match.group('timestamp'), self.tsformat)
		)
            except ValueError:
                continue
            self.send("{} {} {}\n".format(self.key, val, timestamp))
            # re-open the file every minute,
            # cause we don't want to hold open old files

    def send(self, data):
        """
        send data, reconnecting if needed
        """
        while True:
            try:
                return self.conn.send(data)
            except socket.timeout:
                return
            except Exception:
                pass
            # we got an error sending the data
            # close connection
            try:
                self.conn.close()
            except Exception, e:
                print "err closing connection", err
            # reconnect and try again
            try:
                self.conn = socket.create_connection(self.addr)
                continue
            except Exception:
                pass

if __name__ == "__main__":
    try:
	main()
    except KeyboardInterrupt:
	pass

