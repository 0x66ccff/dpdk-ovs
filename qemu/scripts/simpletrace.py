#!/usr/bin/env python
#
# Pretty-printer for simple trace backend binary trace files
#
# Copyright IBM, Corp. 2010
#
# This work is licensed under the terms of the GNU GPL, version 2.  See
# the COPYING file in the top-level directory.
#
# For help see docs/tracing.txt

import struct
import re
import inspect
from tracetool import _read_events, Event
from tracetool.backend.simple import is_string

header_event_id = 0xffffffffffffffff
header_magic    = 0xf2b177cb0aa429b4
dropped_event_id = 0xfffffffffffffffe

log_header_fmt = '=QQQ'
rec_header_fmt = '=QQII'

def read_header(fobj, hfmt):
    '''Read a trace record header'''
    hlen = struct.calcsize(hfmt)
    hdr = fobj.read(hlen)
    if len(hdr) != hlen:
        return None
    return struct.unpack(hfmt, hdr)

def get_record(edict, rechdr, fobj):
    """Deserialize a trace record from a file into a tuple (event_num, timestamp, arg1, ..., arg6)."""
    if rechdr is None:
        return None
    rec = (rechdr[0], rechdr[1])
    if rechdr[0] != dropped_event_id:
        event_id = rechdr[0]
        event = edict[event_id]
        for type, name in event.args:
            if is_string(type):
                l = fobj.read(4)
                (len,) = struct.unpack('=L', l)
                s = fobj.read(len)
                rec = rec + (s,)
            else:
                (value,) = struct.unpack('=Q', fobj.read(8))
                rec = rec + (value,)
    else:
        (value,) = struct.unpack('=Q', fobj.read(8))
        rec = rec + (value,)
    return rec


def read_record(edict, fobj):
    """Deserialize a trace record from a file into a tuple (event_num, timestamp, arg1, ..., arg6)."""
    rechdr = read_header(fobj, rec_header_fmt)
    return get_record(edict, rechdr, fobj) # return tuple of record elements

def read_trace_file(edict, fobj):
    """Deserialize trace records from a file, yielding record tuples (event_num, timestamp, arg1, ..., arg6)."""
    header = read_header(fobj, log_header_fmt)
    if header is None or \
       header[0] != header_event_id or \
       header[1] != header_magic:
        raise ValueError('Not a valid trace file!')
    if header[2] != 0 and \
       header[2] != 2:
        raise ValueError('Unknown version of tracelog format!')

    log_version = header[2]
    if log_version == 0:
        raise ValueError('Older log format, not supported with this QEMU release!')

    while True:
        rec = read_record(edict, fobj)
        if rec is None:
            break

        yield rec

class Analyzer(object):
    """A trace file analyzer which processes trace records.

    An analyzer can be passed to run() or process().  The begin() method is
    invoked, then each trace record is processed, and finally the end() method
    is invoked.

    If a method matching a trace event name exists, it is invoked to process
    that trace record.  Otherwise the catchall() method is invoked."""

    def begin(self):
        """Called at the start of the trace."""
        pass

    def catchall(self, event, rec):
        """Called if no specific method for processing a trace event has been found."""
        pass

    def end(self):
        """Called at the end of the trace."""
        pass

def process(events, log, analyzer):
    """Invoke an analyzer on each event in a log."""
    if isinstance(events, str):
        events = _read_events(open(events, 'r'))
    if isinstance(log, str):
        log = open(log, 'rb')

    enabled_events = []
    dropped_event = Event.build("Dropped_Event(uint64_t num_events_dropped)")
    edict = {dropped_event_id: dropped_event}

    for e in events:
        if 'disable' not in e.properties:
            enabled_events.append(e)
    for num, event in enumerate(enabled_events):
        edict[num] = event

    def build_fn(analyzer, event):
        if isinstance(event, str):
            return analyzer.catchall

        fn = getattr(analyzer, event.name, None)
        if fn is None:
            return analyzer.catchall

        event_argcount = len(event.args)
        fn_argcount = len(inspect.getargspec(fn)[0]) - 1
        if fn_argcount == event_argcount + 1:
            # Include timestamp as first argument
            return lambda _, rec: fn(*rec[1:2 + event_argcount])
        else:
            # Just arguments, no timestamp
            return lambda _, rec: fn(*rec[2:2 + event_argcount])

    analyzer.begin()
    fn_cache = {}
    for rec in read_trace_file(edict, log):
        event_num = rec[0]
        event = edict[event_num]
        if event_num not in fn_cache:
            fn_cache[event_num] = build_fn(analyzer, event)
        fn_cache[event_num](event, rec)
    analyzer.end()

def run(analyzer):
    """Execute an analyzer on a trace file given on the command-line.

    This function is useful as a driver for simple analysis scripts.  More
    advanced scripts will want to call process() instead."""
    import sys

    if len(sys.argv) != 3:
        sys.stderr.write('usage: %s <trace-events> <trace-file>\n' % sys.argv[0])
        sys.exit(1)

    events = _read_events(open(sys.argv[1], 'r'))
    process(events, sys.argv[2], analyzer)

if __name__ == '__main__':
    class Formatter(Analyzer):
        def __init__(self):
            self.last_timestamp = None

        def catchall(self, event, rec):
            i = 1
            timestamp = rec[1]
            if self.last_timestamp is None:
                self.last_timestamp = timestamp
            delta_ns = timestamp - self.last_timestamp
            self.last_timestamp = timestamp

            fields = [event.name, '%0.3f' % (delta_ns / 1000.0)]
            for type, name in event.args:
                if is_string(type):
                    fields.append('%s=%s' % (name, rec[i + 1]))
                else:
                    fields.append('%s=0x%x' % (name, rec[i + 1]))
                i += 1
            print ' '.join(fields)

    run(Formatter())
