#! /usr/bin/python3
# coding: utf-8

import sys
import multiprocessing
import multiprocessing.connection
import random
import socket
import struct
import ast
import time
import logging
import errno
log = logging.getLogger('Media')

class Media(multiprocessing.Process):
    def __init__(self, localip, localport, rtp, owner=None):
        self.localip = localip
        self.localport = localport or 0
        self.remoteip = None
        self.remoteport = None
        if rtp is None:
            self.rtp = None
            self.codecs = []
            for payloadtype,(codecname, codecformat) in RTPStream.defaultcodecs.items():
                self.codecs.append((payloadtype, codecname, codecformat))
        else:
            if isinstance(rtp, RTPStream):
                self.rtp = rtp
            else:
                self.rtp = RTPFile(rtp)
            self.codecs = [self.rtp.codec]
        self.owner = owner or '0.0.0.0'
        self.pipe,self.childpipe = multiprocessing.Pipe()

        multiprocessing.Process.__init__(self, daemon=True)
        self.transmitting = False
        self.start()
        ret = self.pipe.recv()
        if not isinstance(ret, int):
            log.error(ret)
            raise ret
        self.localport = ret
        log.debug("%s starting process %d", self, self.pid)

    def __str__(self):
        return "{}:{}".format(self.localip, self.localport)

    @property
    def localoffer(self):
        sdplines = ['v=0',
                    'o=- {0} {0} IN IP4 {1}'.format(random.randint(0,0xffffffff), self.owner),
                    's=-',
                    'c=IN IP4 {}'.format(self.localip),
                    't=0 0',
                    'm=audio {} RTP/AVP {}'.format(self.localport, ' '.join([str(t) for t,n,f in self.codecs])),
                    'a=sendrecv'
]
        sdplines.extend(['a=rtpmap:{} {}'.format(t, n) for t,n,f in self.codecs if n])
        sdplines.extend(['a=fmtp:{} {}'.format(t, f) for t,n,f in self.codecs if f])
        sdplines.append('')
        return '\r\n'.join(sdplines)

    def setparticipantoffer(self, sdp):
        if self.transmitting:
            return
        for line in sdp.splitlines():
            if line.startswith(b'c='):
                self.remoteip = line.split()[2]
            if line.startswith(b'm='):
                self.remoteport = int(line.split()[1])

    def transmit(self):
        if self.transmitting:
            return
        self.transmitting = True
        if self.remoteip is not None and self.remoteport is not None:
            self.pipe.send((self.remoteip, self.remoteport))
        else:
            log.warning("missing participant offer")

    def stop(self):
        self.pipe.send(None)

    def wait(self):
        self.pipe.recv()

    def run(self):
        # create socket
        # bind it
        # get binded port and send it to parent process
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.localip, self.localport))
        except OSError as err:
            exc = Exception("cannot bind UDP socket to {}. errno={}".format(self.localip, errno.errorcode[err.errno]))
            self.childpipe.send(exc)
            return
        except Exception as e:
            self.childpipe.send(e)
            return
        self.localport = sock.getsockname()[1]
        self.childpipe.send(self.localport)

        # wait for parent process to give remote address
        remoteaddr = self.childpipe.recv()
        if not remoteaddr:
            self.childpipe.send(None)
            return

        # send content of RTP file and discard incoming datagrams
        wakeuptime = time.monotonic() # initial wakeup time is now
        running = True
        log.info("%s Starting", self)
        while running:
            currenttime = time.monotonic()
            if self.rtp is None:
                sleep = None
            elif wakeuptime <= currenttime:
                sleep = 0
            else:
                sleep = wakeuptime - currenttime

            # wait for incoming data from socket or wakeup time
            obj = None
            for obj in multiprocessing.connection.wait([sock, self.childpipe], sleep):
                if obj == sock:
                    # incoming data
                    buf,addr = sock.recvfrom(65536)
                    rtp = RTP.frombytes(buf)
                    log.info("%s <-- %s", self, rtp)
                elif obj == self.childpipe:
                    self.childpipe.recv()
                    running = False
            if obj is None:
                # time to send next RTP packet if there is one
                if not self.rtp.eof:
                    rtp,duration = self.rtp.nextpacket()
                    sock.sendto(rtp.tobytes(), remoteaddr)
                    log.info("%s --> %s", self, rtp)
                    wakeuptime += duration

        # unlock waiting parent process
        self.childpipe.send(None)
        log.info("%s Stopping", self)

class RTP:
    def __init__(self, payload, PT, seq, TS, SSRC, version=2, P=0, X=0, CC=0, M=0):
        self.payload = payload
        self.PT = PT
        self.seq = seq
        self.TS = TS
        self.SSRC = SSRC
        self.version,self.P,self.X,self.CC,self.M = version,P,X,CC,M

    def __str__(self):
        return "PT={} seq=0x{:x} TS=0x{:x} SSRC=0x{:x} + {}bytes".format(self.PT, self.seq, self.TS, self.SSRC, len(self.payload))

    @staticmethod
    def frombytes(buf):
        h0,h1,seq,TS,SSRC = struct.unpack_from('!bbHLL', buf[:12] + 12*b'\x00')
        version = h0>>6
        P = (h0>>5) & 0b1
        X = (h0>>4) & 0b1
        CC = h0 & 0b1111
        M = h1 >> 7
        PT = h1 & 0b01111111
        payload = buf[12:]

        return RTP(payload, PT, seq, TS, SSRC, version, P, X, CC, M)

    def tobytes(self):
        hdr = bytearray(12)
        hdr[0] = self.version<<6 | self.P<<5 | self.X<<4 | self.CC
        hdr[1] = self.M<<7 | self.PT
        struct.pack_into('!HLL', hdr, 2, self.seq, self.TS, self.SSRC)
        return hdr + self.payload
        

class RTPStream:
    defaultcodecs = {
        0 :('PCMU/8000',   None),
        3 :('GSM/8000',    None),
        4 :('G723/8000',   None),
        5 :('DVI4/8000',   None),
        6 :('DVI4/16000',  None),
        7 :('LPC/8000',    None),
        8 :('PCMA/8000',   None),
        9 :('G722/8000',   None),
        10:('L16/44100/2', None),
        11:('L16/44100/1', None),
        12:('QCELP/8000',  None),
        13:('CN/8000',     None),
        14:('MPA/90000',   None),
        15:('G728/8000',   None),
        16:('DVI4/11025',  None),
        17:('DVI4/22050',  None),
        18:('G729/8000',   None)}

    def __init__(self, PT, rtplen, **params):
        self.PT = PT
        self.rtplen = rtplen
        if self.PT in RTPStream.defaultcodecs:
            self.codec = [self.PT, *RTPStream.defaultcodecs[self.PT]]
        else:
            self.codec = [self.PT, None, None]
        if 'codecname' in params:
            self.codec[1] = params.pop('codecname')
        if 'codecformat' in params:
            self.codec[2] = params.pop('codecformat')
        if self.codec[1] is None:
            raise Exception("missing codecname")

        self.seq = params.pop('seq', random.randint(0,0xffff))
        self.period = params.pop('period', 0.020)
        self.SSRC = params.pop('SSRC', random.randint(0,0xffffffff))
        self.TS = params.pop('TS', random.randint(0,0xffffffff))
        self.numsamples = params.pop('numsamples', None)
        if self.numsamples is None:
            try:
                samplingrate = int(self.codec[1].split('/')[1])
                self.numsamples = int(samplingrate * self.period)
            except:
                raise Exception("missing 'timestamp' or 'numsamples' or sampling rate in codec name")
        self.eof = True

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    def nextparams(self):
        self.TS = (self.TS + self.numsamples)  % 0xffffffff
        self.seq = (self.seq + 1) % 0xffff

    def nextpayload(self):
        return b''

    def nextpacket(self):
        rtp = RTP(self.nextpayload(), self.PT, self.seq, self.TS, self.SSRC)

        self.nextparams()
        return rtp, self.period

class RTPFile(RTPStream):
    def __init__(self, rtpfile):
        RTPStream.__init__(self)
        self.eof = False
        if isinstance(rtpfile, str):
            self.f = open(rtpfile, 'rb')
            self.name = rtpfile
        else:
            self.f = rtpfile
            try:
                self.name = f.name
            except:
                pass
        self.nextparams()

    def readupto(self, mark):
        buf = bytearray()
        while True:
            b = self.f.read(1)
            if not b:
                self.eof = True
                return b''
            buf += b
            if buf.endswith(mark):
                break
        return bytes(buf[:-len(mark)])

    def nextpayload(self):
        return self.readupto(b'>>>>')

    def nextparams(self):
        parambuf = self.readupto(b'<<<<')

        # read parameters
        params = {}
        for line in parambuf.splitlines():
            # discard comment lines
            if line.strip().startswith(b'#'):
                continue
            # parameter line is <key> = <value>, ignore others
            try:
                k,v = line.split(b'=', 1)
                params[k.strip().decode('utf-8')] = ast.literal_eval(v.strip().decode('utf-8'))
            except Exception as e:
                pass
        if params:
            log.debug("%s params=%s", self, params)

        # update stored values
        dseq = params.pop('dseq', 1)
        if 'seq' in params:
            self.seq = params.pop('seq')
        else:
            self.seq = (self.seq + dseq) % 0xffff

        if 'PT' in params:
            self.PT = params.pop('PT')
            if self.PT in RTPStream.defaultcodecs:
                self.codec = [self.PT, *RTPStream.defaultcodecs[self.PT]]
            else:
                self.codec = [self.PT, None, None]
        if 'codecname' in params:
            self.codec[1] = params.pop('codecname')
        if 'codecformat' in params:
            self.codec[2] = params.pop('codecformat')
        if self.PT is None:
            raise Exception("missing PT param in {}".format(self))
        if self.codec[1] is None:
            raise Exception("missing codecname for PT={} in {}".format(self.PT, self))

        self.period = params.pop('period', self.period)
        if 'timestamp' in params:
            self.TS = params.pop('TS')
        else:
            if 'numsamples' in params:
                self.numsamples = params.pop('numsamples')
            if self.numsamples is None:
                try:
                    samplingrate = int(self.codec[1].split('/')[1])
                    self.numsamples = int(samplingrate * self.period)
                except:
                    raise Exception("cannot compute TS. Missing 'timestamp' or 'numsamples' or sampling rate in codec name in {}".format(self))
            self.TS = (self.TS + self.numsamples)  % 0xffffffff

        self.__dict__.update(params)

class RTPRandomStream(RTPStream):
    def __init__(self, PT, rtplen, **params):
        RTPStream.__init__(self, PT, rtplen, **params)
        self.eof = False

    def nextpayload(self):
        return bytes((random.choice(range(256)) for _ in range(self.rtplen)))


if __name__ == '__main__':
    import tempfile
    import os

    import snl
    snl.loggers['Media'].setLevel('DEBUG')

    fd,name = tempfile.mkstemp()
    f = open(fd, 'wb')
    f.write(b"""
PT=0
seq=0x100
<<<<0123>>>>
<<<<4567>>>>

#simulating packet lost
dseq=2
<<<<abc>>>>
<<<<def>>>>
""")
    f.close()

    media = Media('127.0.0.1', name)
    media.setparticipantoffer(b'''v=0\r
o=- 123 123 IN IP4 toto\r
s=-
m=audio 12345 RTP/AVP 116\r
c=IN IP4 127.0.0.1\r
a=rtpmap:116 AMR-WB/16000/1\r
''')
    media.transmit()
    media.wait()
    os.remove(name)

    s = RTPRandomStream(PT=10, rtplen=40)
    for _ in range(20):
        s.nextpacket()
