graphitetailer
==============

Tail logs to stream data to graphite

Description
-----------


tail.py is a python script that tails a log file,
parses out a floating point value and a timestamp
and sends the output to graphite.

Example
--------

Assume you have a log formatted like:

	GET / HTTP/1.0 requesttime=1,000ms [23/Aug/2010:03:50:59 +0000]

You want to send the metric 1000 and the timestamp to graphite under the key "webserver.request.duration".
'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*in (?P<duration>[0-9,]+)ms'
First you have to have a regex for parsing out the timestamp and duration. This uses python named capture groups.

	requesttime=(?P<duration>[0-9,]+)ms \[(?P<timestamp>.*?)\]

You also need to inform python how to parse your timestamp:
    --tsformat '%d/%b/%Y:%H:%M:%S %z'
Finally add a metric key
    --key "webserver.request.duration"

Test this by running nc -lk 2003 in another terminal

Run

	echo "GET / HTTP/1.0 requesttime=1,000ms [23/Aug/2010:03:50:59 +0000]" >out.log
    ./tail.py  --tsformat '%d/%b/%Y:%H:%M:%S %z' --key "webserver.request.duration" 'requesttime=(?P<duration>[0-9,]+)ms \[(?P<timestamp>.*?)\]' out.log

