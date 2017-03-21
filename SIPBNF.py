#coding: utf-8

import collections

import pyparsing as pp

class ParseException(Exception):
    def __init__(self, msg, pos):
        self.msg = msg
        self.pos = pos

class Parser:
    def __init__(self, ppParser):
        self.parser = ppParser + pp.StringEnd()
        self.parser.leaveWhitespace()
        self.parser.setWhitespaceChars('')
        self.parser.parseWithTabs()
    def parse(self, string):
        try:
            return self.parser.parseString(string)
        except pp.ParseException as e:
            raise ParseException(e.msg, pos=e.col-1)

#   Even though an arbitrary number of parameter pairs may be attached to
#   a header field value, any given parameter-name MUST NOT appear more
#   than once.
#
#   When comparing header fields, field names are always case-
#   insensitive.  Unless otherwise stated in the definition of a
#   particular header field, field values, parameter names, and parameter
#   values are case-insensitive.


#   Several rules are incorporated from RFC 2396 [5] but are updated to
#   make them compliant with RFC 2234 [10].  These include:
#
#      reserved    =  ";" / "/" / "?" / ":" / "@" / "&" / "=" / "+"
#                     / "$" / ","
#      unreserved  =  alphanum / mark
#      mark        =  "-" / "_" / "." / "!" / "~" / "*" / "'"
#                     / "(" / ")"
#      escaped     =  "%" HEXDIG HEXDIG
HEXDIG = pp.hexnums
unreserved  =  pp.alphanums + '-_.!~*\'()'
escaped = pp.Literal('%') + pp.Word(HEXDIG, exact=2)
reserved =  ';/?:@&=+$,'


#   SIP header field values can be folded onto multiple lines if the
#   continuation line begins with a space or horizontal tab.  All linear
#   white space, including folding, has the same semantics as SP.  A
#   recipient MAY replace any linear white space with a single SP before
#   interpreting the field value or forwarding the message downstream.
#   This is intended to behave exactly as HTTP/1.1 as described in RFC
#   2616 [8].  The SWS construct is used when linear white space is
#   optional, generally between tokens and separators.
#
#      LWS  =  [*WSP CRLF] 1*WSP ; linear whitespace
#      SWS  =  [LWS] ; sep whitespace
WSP = pp.Word(' \t')
LWS = WSP.setName('LWS')
SWS = pp.Optional(WSP).setName('SWS')


#   To separate the header name from the rest of value, a colon is used,
#   which, by the above rule, allows whitespace before, but no line
#   break, and whitespace after, including a linebreak.  The HCOLON
#   defines this construct.
#
#      HCOLON  =  *( SP / HTAB ) ":" SWS
CRLF = pp.Literal('\r\n')
HCOLON = pp.Group(pp.Optional(WSP) + pp.Literal(':') + pp.Optional(WSP) + pp.Optional(CRLF) + pp.Optional(WSP))


#   The TEXT-UTF8 rule is only used for descriptive field contents and
#   values that are not intended to be interpreted by the message parser.
#   Words of *TEXT-UTF8 contain characters from the UTF-8 charset (RFC
#   2279 [7]).  The TEXT-UTF8-TRIM rule is used for descriptive field
#   contents that are n t quoted strings, where leading and trailing LWS
#   is not meaningful.  In this regard, SIP differs from HTTP, which uses
#   the ISO 8859-1 character set.
#
#      TEXT-UTF8-TRIM  =  1*TEXT-UTF8char *(*LWS TEXT-UTF8char)
#      TEXT-UTF8char   =  %x21-7E / UTF8-NONASCII
#      UTF8-NONASCII   =  %xC0-DF 1UTF8-CONT
#                      /  %xE0-EF 2UTF8-CONT
#                      /  %xF0-F7 3UTF8-CONT
#                      /  %xF8-Fb 4UTF8-CONT
#                      /  %xFC-FD 5UTF8-CONT
#      UTF8-CONT       =  %x80-BF
#
#  A CRLF is allowed in the definition of TEXT-UTF8-TRIM only as part of
#   a header field continuation.  It is expected that the folding LWS
#   will be replaced with a single SP before interpretation of the TEXT-
#   UTF8-TRIM value.
#
#   Hexadecimal numeric characters are used in several protocol elements.
#   Some elements (authentication) force hex alphas to be lower case.
#
#      LHEX  =  DIGIT / %x61-66 ;lowercase a-f
LHEX = '0123456789abcdef'


#   Many SIP header field values consist of words separated by LWS or
#   special characters.  Unless otherwise stated, tokens are case-
#   insensitive.  These special characters MUST be in a quoted string to
#   be used within a parameter value.  The word construct is used in
#   Call-ID to allow most separators to be used.
#
#      token       =  1*(alphanum / "-" / "." / "!" / "%" / "*"
#                     / "_" / "+" / "`" / "'" / "~" )
#      separators  =  "(" / ")" / "<" / ">" / "@" /
#                     "," / ";" / ":" / "\" / DQUOTE /
#                     "/" / "[" / "]" / "?" / "=" /
#                     "{" / "}" / SP / HTAB
#      word        =  1*(alphanum / "-" / "." / "!" / "%" / "*" /
#                     "_" / "+" / "`" / "'" / "~" /
#                     "(" / ")" / "<" / ">" /
#                     ":" / "\" / DQUOTE /
#                     "/" / "[" / "]" / "?" /
#                     "{" / "}" )
token = pp.Word(pp.alphanums + '-.!%*_+`\'~', min=1)
word  = pp.Word(pp.alphanums + '-.!%*_+`\'~()<>:\\"/[]?{}', min=1)

#   When tokens are used or separators are used between elements,
#   whitespace is often allowed before or after these characters:
#
#      STAR    =  SWS "*" SWS ; asterisk
#      SLASH   =  SWS "/" SWS ; slash
#      EQUAL   =  SWS "=" SWS ; equal
#      LPAREN  =  SWS "(" SWS ; left parenthesis
#      RPAREN  =  SWS ")" SWS ; right parenthesis
#      RAQUOT  =  ">" SWS ; right angle quote
#      LAQUOT  =  SWS "<"; left angle quote
#      COMMA   =  SWS "," SWS ; comma
#      SEMI    =  SWS ";" SWS ; semicolon
#      COLON   =  SWS ":" SWS ; colon
#      LDQUOT  =  SWS DQUOTE; open double quotation mark
#      RDQUOT  =  DQUOTE SWS ; close double quotation mark
SLASH = (pp.Suppress(SWS) + pp.Literal('/') + pp.Suppress(SWS)).setName('SLASH')
EQUAL = (pp.Suppress(SWS) + pp.Literal('=') + pp.Suppress(SWS)).setName('EQUAL')


RAQUOT = pp.Literal(">") + pp.Suppress(SWS)
LAQUOT = pp.Suppress(SWS) + pp.Literal("<")
COMMA = pp.Suppress(SWS + pp.Literal(',') + SWS).setName('COMMA')
SEMI = pp.Suppress(SWS + pp.Literal(';') + SWS).setName('SEMI')
COLON = (pp.Suppress(SWS) + pp.Literal(':') + pp.Suppress(SWS)).setName('COLON')
DQUOTE = pp.Literal('"').setName('DQUOTE')
LDQUOT = SWS + DQUOTE
RDQUOT = DQUOTE + SWS


#  Comments can be included in some SIP header fields by surrounding the
#   comment text with parentheses.  Comments are only allowed in fields
#   containing "comment" as part of their field value definition.  In all
#   other fields, parentheses are considered part of the field value.
#
#      comment  =  LPAREN *(ctext / quoted-pair / comment) RPAREN
#      ctext    =  %x21-27 / %x2A-5B / %x5D-7E / UTF8-NONASCII
#                  / LWS
#
#   ctext includes all chars except left and right parens and backslash.
#   A string of text is parsed as a single word if it is quoted using
#   double-quote marks.  In quoted strings, quotation marks (") and
#   backslashes (\) need to be escaped.
#
#     quoted-string  =  SWS DQUOTE *(qdtext / quoted-pair ) DQUOTE
#      qdtext         =  LWS / %x21 / %x23-5B / %x5D-7E
#                        / UTF8-NONASCII
#
#   The backslash character ("\") MAY be used as a single-character
#   quoting mechanism only within quoted-string and comment constructs.
#   Unlike HTTP/1.1, the characters CR and LF cannot be escaped by this
#   mechanism to avoid conflict with line folding and header separation.
#
#quoted-pair  =  "\" (%x00-09 / %x0B-0C
#                / %x0E-7F)
qdtext = pp.Word(pp.srange('[\x20-\x7e]'), excludeChars='\x22\x5c')
qdtext = pp.Word(pp.printables+' \t', excludeChars='"\\')
qdtext = pp.Word(pp.srange('[\x20-\xff]'), excludeChars='\x22\x5c')
qdtext = pp.Word(pp.srange(r'[\x20-\xff]'), excludeChars='"\\')
#qdtext = pp.Word(pp.printables+' \t', excludeChars='"\\')
#qdtext = pp.Regex('[^"]*')
quoted_pair = pp.Literal('\\') + pp.Word(pp.srange('[\x00-\x7f]'), excludeChars='\x0a\x0d', min=1, max=1)
quoted_string = pp.Combine(pp.Suppress(SWS) + DQUOTE + pp.ZeroOrMore(qdtext ^ quoted_pair) + DQUOTE).setName('quoted-string')
      

#SIP-URI          =  "sip:" [ userinfo ] hostport
#                    uri-parameters [ headers ]
#SIPS-URI         =  "sips:" [ userinfo ] hostport
#                    uri-parameters [ headers ]
#userinfo         =  ( user / telephone-subscriber ) [ ":" password ] "@"
#user             =  1*( unreserved / escaped / user-unreserved )
#user-unreserved  =  "&" / "=" / "+" / "$" / "," / ";" / "?" / "/"
#password         =  *( unreserved / escaped /
#                    "&" / "=" / "+" / "$" / "," )
#hostport         =  host [ ":" port ]
#host             =  hostname / IPv4address / IPv6reference
#hostname         =  *( domainlabel "." ) toplabel [ "." ]
#domainlabel      =  alphanum
#                    / alphanum *( alphanum / "-" ) alphanum
#toplabel         =  ALPHA / ALPHA *( alphanum / "-" ) alphanum
#IPv4address    =  1*3DIGIT "." 1*3DIGIT "." 1*3DIGIT "." 1*3DIGIT
#IPv6reference  =  "[" IPv6address "]"
#IPv6address    =  hexpart [ ":" IPv4address ]
#hexpart        =  hexseq / hexseq "::" [ hexseq ] / "::" [ hexseq ]
#hexseq         =  hex4 *( ":" hex4)
#hex4           =  1*4HEXDIG
#port           =  1*DIGIT
#
#   The BNF for telephone-subscriber can be found in RFC 2806 [9].  Note,
#   however, that any characters allowed there that are not allowed in
#   the user part of the SIP URI MUST be escaped.
#
#uri-parameters    =  *( ";" uri-parameter)
#uri-parameter     =  transport-param / user-param / method-param
#                     / ttl-param / maddr-param / lr-param / other-param
#transport-param   =  "transport="
#                     ( "udp" / "tcp" / "sctp" / "tls"
#                     / other-transport)
#other-transport   =  token
#user-param        =  "user=" ( "phone" / "ip" / other-user)
#other-user        =  token
#method-param      =  "method=" Method
#ttl-param         =  "ttl=" ttl
#maddr-param       =  "maddr=" host
#lr-param          =  "lr"
#other-param       =  pname [ "=" pvalue ]
#pname             =  1*paramchar
#pvalue            =  1*paramchar
#paramchar         =  param-unreserved / unreserved / escaped
#param-unreserved  =  "[" / "]" / "/" / ":" / "&" / "+" / "$"
#
#headers         =  "?" header *( "&" header )
#header          =  hname "=" hvalue
#hname           =  1*( hnv-unreserved / unreserved / escaped )
#hvalue          =  *( hnv-unreserved / unreserved / escaped )
#hnv-unreserved  =  "[" / "]" / "/" / "?" / ":" / "+" / "$"
user = pp.OneOrMore(pp.Word(unreserved+'&=+$,;?/') ^ escaped)
password = pp.ZeroOrMore(pp.Word(unreserved+'&=+$,') ^ escaped)
userinfo = user + pp.Optional(pp.Suppress(pp.Literal(':')) + password, None) + pp.Suppress(pp.Literal('@'))
domainlabel = pp.Word(pp.alphanums) ^ (pp.Word(pp.alphanums, pp.alphanums + '-') + pp.Word(pp.alphanums))
toplabel = pp.Word(pp.alphas) ^ (pp.Word(pp.alphas, pp.alphanums + '-') + pp.Word(pp.alphanums))
hostname = pp.Combine(pp.ZeroOrMore(domainlabel + pp.Literal('.')) + toplabel + pp.Optional(pp.Literal('.')))
IPv4address = pp.Combine(pp.Word(pp.nums, max=3) + pp.Literal('.') + pp.Word(pp.nums, max=3) + pp.Literal('.') + pp.Word(pp.nums, max=3) + pp.Literal('.') + pp.Word(pp.nums, max=3))
hex4 = pp.Word(HEXDIG, max=4)
hexseq =  hex4 + pp.ZeroOrMore(pp.Literal(':') + hex4)
hexpart =  hexseq ^ (hexseq + pp.Literal('::') + pp.Optional(hexseq)) ^ (pp.Literal('::') + pp.Optional(hexseq))
IPv6address =  pp.Combine(hexpart + pp.Optional(pp.Literal(':') + IPv4address))
IPv6reference = pp.Combine(pp.Literal('[') + IPv6address +pp.Literal(']'))
host =  hostname ^ IPv4address ^ IPv6reference
hostport =  host + pp.Optional(pp.Suppress(pp.Literal(':')) + pp.Word(pp.nums), '')
other_transport = token
transport_param = pp.CaselessLiteral('transport=') + (pp.CaselessLiteral('udp') ^ pp.CaselessLiteral('tcp') ^ pp.CaselessLiteral('sctp') ^ pp.CaselessLiteral('tls') ^ other_transport)
other_user =  token
user_param =  pp.CaselessLiteral('user') + pp.Literal('=') + (pp.CaselessLiteral('phone') ^ pp.CaselessLiteral('ip') ^ other_user)
method_param = pp.CaselessLiteral('method') + pp.Literal('=') + (pp.Literal('INVITE') ^ pp.Literal('ACK') ^ pp.Literal('OPTIONS') ^ pp.Literal('BYE') ^ pp.Literal('CANCEL') ^ pp.Literal('REGISTER') ^ token)
ttl_param = pp.CaselessLiteral('ttl') + pp.Literal('=') + pp.Word(pp.nums, max=3)
maddr_param = pp.CaselessLiteral('maddr') + pp.Literal('=') + host
lr_param = pp.CaselessLiteral('lr')
pvalue = pname = pp.OneOrMore(pp.Word(unreserved+'[]/:&+$') ^ escaped)
other_param = pname + pp.Optional(pp.Literal('=') + pvalue)
uri_parameter = transport_param ^ user_param ^ method_param ^ ttl_param ^ maddr_param ^ lr_param ^ other_param
uri_parameters = pp.ZeroOrMore(pp.Literal(';') + uri_parameter)
hvalue = pp.ZeroOrMore(pp.Word(unreserved+'[]/?:+$') ^ escaped)
hname = pp.OneOrMore(pp.Word(unreserved+'[]/?:+$') ^ escaped)
header = hname + pp.Literal('=') + hvalue
headers = pp.Literal('?') + header + pp.ZeroOrMore(pp.Literal('&') + header)

SIP_URI  = pp.CaselessLiteral('sip')  + pp.Suppress(pp.Literal(':')) + pp.Optional(userinfo, None) + hostport + uri_parameters + pp.Optional(headers)
SIPS_URI = pp.CaselessLiteral('sips') + pp.Suppress(pp.Literal(':'))+ pp.Optional(userinfo, None) + hostport + uri_parameters + pp.Optional(headers)


#SIP-message    =  Request / Response
#Request        =  Request-Line
#                  *( message-header )
#                  CRLF
#                  [ message-body ]
#Request-Line   =  Method SP Request-URI SP SIP-Version CRLF
#Request-URI    =  SIP-URI / SIPS-URI / absoluteURI
#absoluteURI    =  scheme ":" ( hier-part / opaque-part )
#hier-part      =  ( net-path / abs-path ) [ "?" query ]
#net-path       =  "//" authority [ abs-path ]
#abs-path       =  "/" path-segments
#opaque-part    =  uric-no-slash *uric
#uric           =  reserved / unreserved / escaped
#uric-no-slash  =  unreserved / escaped / ";" / "?" / ":" / "@"
#                  / "&" / "=" / "+" / "$" / ","
#path-segments  =  segment *( "/" segment )
#segment        =  *pchar *( ";" param )
#param          =  *pchar
#pchar          =  unreserved / escaped /
#                  ":" / "@" / "&" / "=" / "+" / "$" / ","
#scheme         =  ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
#authority      =  srvr / reg-name
#srvr           =  [ [ userinfo "@" ] hostport ] !!!! @ already in userinfo !!!!
#reg-name       =  1*( unreserved / escaped / "$" / ","
#                  / ";" / ":" / "@" / "&" / "=" / "+" )
#query          =  *uric
uric = pp.ZeroOrMore(pp.Word(unreserved+reserved) ^ escaped)
opaque_part = pp.Combine((pp.Word(unreserved+';?:@&=+$,', max=1) ^ escaped) + uric)
query = uric
pchar = pp.ZeroOrMore(pp.Word(unreserved+':@&=+$,') ^ escaped)
segment = pchar + pp.ZeroOrMore(pp.Literal(';') + pchar)
path_segments = segment + pp.ZeroOrMore(pp.Literal('/') + segment)
abs_path = pp.Literal('/') + path_segments
reg_name = pp.OneOrMore(pp.Word(unreserved+'$,;:@&=+') ^ escaped)
srvr = pp.Optional(pp.Optional(userinfo) + hostport)
authority = srvr ^ reg_name
net_path = pp.Literal('//') + authority + pp.Optional(abs_path)
hier_part = pp.Combine(net_path ^ abs_path) + pp.Optional(pp.Literal('?') + pp.Combine(query))
scheme = pp.Word(pp.alphas, pp.alphanums+'+-.')
absoluteURI = scheme + pp.Suppress(pp.Literal(':')) + (hier_part ^ opaque_part)
Request_URI = SIP_URI ^ SIPS_URI ^ absoluteURI

class URI:
    def __init__(self, value):
        res = Parser(Request_URI).parse(value)
        self.scheme = res.pop(0)
        if self.scheme.startswith('sip'):
            # SIP or SIPS URI
            self.user = res.pop(0)
            if self.user is None:
                self.password = None
            else:
                self.password = res.pop(0)
            self.host = res.pop(0)
            port = res.pop(0)
            if port == '':
                self.port = None
            else:
                self.port = int(port)
            self.parameters = collections.OrderedDict()
            while res and res[0] == ';':
                res.pop(0)
                k = res.pop(0)
                if res and res[0] == '=':
                    res.pop(0)
                    v = res.pop(0)
                else:
                    v = None
                self.parameters[k] = v
            self.headers = collections.OrderedDict()
            if res:
                res.pop(0) # it should be a '?'
            while res:
                k = res.pop(0)
                res.pop(0) # it should be a '='
                v =res.pop(0)
                self.headers[k] = v
        else:
            # absoluteURI
            self.uri = res.pop(0)
            self.query = res.pop(0) if res else None
        assert len(res) == 0
    @property
    def userinfo(self):
        if self.user is None and self.password is None:
            return ''
        if self.password is None:
            return '{}@'.format(self.user)
        return '{}:{}@'.format(self.user or '', self.password)
    def __str__(self):
        if self.scheme.startswith('sip'):
            if self.port is None:
                hostport = self.host
            else:
                hostport = '{}:{}'.format(self.host, self.port)
            parameters = (';{}{}'.format(k, ('={}'.format(v) if v is not None else '') or '') for k,v in self.parameters.items())
            headers = ('{}={}'.format(k, v) for k,v in self.headers.items())
            return "{}:{}{}{}{}".format(self.scheme, self.userinfo, hostport, ''.join(parameters), '&'.join(headers) or '')
        else:
            return "{}:{}{}".format(self.scheme, self.uri, "?{}".format(self.query) if self.query is not None else '')

#SIP-Version    =  "SIP" "/" 1*DIGIT "." 1*DIGIT
#
#message-header  =  (Accept
#                /  Accept-Encoding
#                /  Accept-Language
#                /  Alert-Info
#                /  Allow
#                /  Authentication-Info
#                /  Authorization
#                /  Call-ID
#                /  Call-Info
#                /  Contact
#                /  Content-Disposition
#                /  Content-Encoding
#                /  Content-Language
#                /  Content-Length
#                /  Content-Type
#                /  CSeq
#                /  Date
#                /  Error-Info
#                /  Expires
#                /  From
#                /  In-Reply-To
#                /  Max-Forwards
#                /  MIME-Version
#                /  Min-Expires
#                /  Organization
#                /  Priority
#                /  Proxy-Authenticate
#                /  Proxy-Authorization
#                /  Proxy-Require
#                /  Record-Route
#                /  Reply-To
#                /  Require
#                /  Retry-After
#                /  Route
#                /  Server
#                /  Subject
#                /  Supported
#                /  Timestamp
#                /  To
#                /  Unsupported
#                /  User-Agent
#                /  Via
#                /  Warning
#                /  WWW-Authenticate
#                /  extension-header) CRLF
#
#INVITEm           =  %x49.4E.56.49.54.45 ; INVITE in caps
#ACKm              =  %x41.43.4B ; ACK in caps
#OPTIONSm          =  %x4F.50.54.49.4F.4E.53 ; OPTIONS in caps
#BYEm              =  %x42.59.45 ; BYE in caps
#CANCELm           =  %x43.41.4E.43.45.4C ; CANCEL in caps
#REGISTERm         =  %x52.45.47.49.53.54.45.52 ; REGISTER in caps
#Method            =  INVITEm / ACKm / OPTIONSm / BYEm
#                     / CANCELm / REGISTERm
#                     / extension-method
#extension-method  =  token
Method = pp.Literal('INVITE') ^ pp.Literal('ACK') ^ pp.Literal('OPTIONS') ^ pp.Literal('BYE') ^ pp.Literal('CANCEL') ^ pp.Literal('REGISTER') ^ token


#Response          =  Status-Line
#                     *( message-header )
#                     CRLF
#                     [ message-body ]
#
#Status-Line     =  SIP-Version SP Status-Code SP Reason-Phrase CRLF
#Status-Code     =  Informational
#               /   Redirection
#               /   Success
#               /   Client-Error
#               /   Server-Error
#               /   Global-Failure
#               /   extension-code
#extension-code  =  3DIGIT
#Reason-Phrase   =  *(reserved / unreserved / escaped
#                   / UTF8-NONASCII / UTF8-CONT / SP / HTAB)
#
#Informational  =  "100"  ;  Trying
#              /   "180"  ;  Ringing
#              /   "181"  ;  Call Is Being Forwarded
#              /   "182"  ;  Queued
#              /   "183"  ;  Session Progress
#
#Success  =  "200"  ;  OK
#
#Redirection  =  "300"  ;  Multiple Choices
#            /   "301"  ;  Moved Permanently
#            /   "302"  ;  Moved Temporarily
#            /   "305"  ;  Use Proxy
#            /   "380"  ;  Alternative Service
#
#Client-Error  =  "400"  ;  Bad Request
#             /   "401"  ;  Unauthorized
#             /   "402"  ;  Payment Required
#             /   "403"  ;  Forbidden
#             /   "404"  ;  Not Found
#             /   "405"  ;  Method Not Allowed
#             /   "406"  ;  Not Acceptable
#             /   "407"  ;  Proxy Authentication Required
#             /   "408"  ;  Request Timeout
#             /   "410"  ;  Gone
#             /   "413"  ;  Request Entity Too Large
#             /   "414"  ;  Request-URI Too Large
#             /   "415"  ;  Unsupported Media Type
#             /   "416"  ;  Unsupported URI Scheme
#             /   "420"  ;  Bad Extension
#             /   "421"  ;  Extension Required
#             /   "423"  ;  Interval Too Brief
#             /   "480"  ;  Temporarily not available
#             /   "481"  ;  Call Leg/Transaction Does Not Exist
#             /   "482"  ;  Loop Detected
#             /   "483"  ;  Too Many Hops
#             /   "484"  ;  Address Incomplete
#             /   "485"  ;  Ambiguous
#             /   "486"  ;  Busy Here
#             /   "487"  ;  Request Terminated
#             /   "488"  ;  Not Acceptable Here
#             /   "491"  ;  Request Pending
#             /   "493"  ;  Undecipherable
#
#Server-Error  =  "500"  ;  Internal Server Error
#             /   "501"  ;  Not Implemented
#             /   "502"  ;  Bad Gateway
#             /   "503"  ;  Service Unavailable
#             /   "504"  ;  Server Time-out
#             /   "505"  ;  SIP Version not supported
#             /   "513"  ;  Message Too Large
#
#Global-Failure  =  "600"  ;  Busy Everywhere
#               /   "603"  ;  Decline
#               /   "604"  ;  Does not exist anywhere
#               /   "606"  ;  Not Acceptable

#Accept         =  "Accept" HCOLON
#                   [ accept-range *(COMMA accept-range) ]
#accept-range   =  media-range *(SEMI accept-param)
#media-range    =  ( "*/*"
#                  / ( m-type SLASH "*" )
#                  / ( m-type SLASH m-subtype )
#                  ) *( SEMI m-parameter )
#accept-param   =  ("q" EQUAL qvalue) / generic-param
#qvalue         =  ( "0" [ "." 0*3DIGIT ] )
#                  / ( "1" [ "." 0*3("0") ] )
#generic-param  =  token [ EQUAL gen-value ]
#gen-value      =  token / host / quoted-string
gen_value = token ^ host ^ quoted_string
generic_param = token + pp.Optional(EQUAL + gen_value)

#Accept-Encoding  =  "Accept-Encoding" HCOLON
#                     [ encoding *(COMMA encoding) ]
#encoding         =  codings *(SEMI accept-param)
#codings          =  content-coding / "*"
#content-coding   =  token
#
#Accept-Language  =  "Accept-Language" HCOLON
#                     [ language *(COMMA language) ]
#language         =  language-range *(SEMI accept-param)
#language-range   =  ( ( 1*8ALPHA *( "-" 1*8ALPHA ) ) / "*" )
#
#Alert-Info   =  "Alert-Info" HCOLON alert-param *(COMMA alert-param)
#alert-param  =  LAQUOT absoluteURI RAQUOT *( SEMI generic-param )
#
#Allow  =  "Allow" HCOLON [Method *(COMMA Method)]


#Authorization     =  "Authorization" HCOLON credentials
#credentials       =  ("Digest" LWS digest-response)
#                     / other-response
#digest-response   =  dig-resp *(COMMA dig-resp)
#dig-resp          =  username / realm / nonce / digest-uri
#                      / dresponse / algorithm / cnonce
#                      / opaque / message-qop
#                      / nonce-count / auth-param
#username          =  "username" EQUAL username-value
#username-value    =  quoted-string
#digest-uri        =  "uri" EQUAL LDQUOT digest-uri-value RDQUOT
#digest-uri-value  =  rquest-uri ; Equal to request-uri as specified
#                     by HTTP/1.1
#message-qop       =  "qop" EQUAL qop-value
#cnonce            =  "cnonce" EQUAL cnonce-value
#cnonce-value      =  nonce-value
#nonce-count       =  "nc" EQUAL nc-value
#nc-value          =  8LHEX
#dresponse         =  "response" EQUAL request-digest
#request-digest    =  LDQUOT 32LHEX RDQUOT
#auth-param        =  auth-param-name EQUAL
#                     ( token / quoted-string )
#auth-param-name   =  token
#other-response    =  auth-scheme LWS auth-param
#                     *(COMMA auth-param)
#auth-scheme       =  token
auth_param_name = token
auth_param = auth_param_name + EQUAL + (token ^ quoted_string)
auth_scheme = token
other_response = auth_scheme + pp.Suppress(LWS) + auth_param + pp.ZeroOrMore(COMMA + auth_param)
digest_uri_value = Request_URI('uri')
digest_uri = pp.CaselessLiteral('uri') + EQUAL + pp.Combine(LDQUOT + digest_uri_value + LDQUOT)
request_digest = pp.Combine(LDQUOT + pp.Optional(pp.Word(LHEX, exact=32)) + RDQUOT)
dresponse =  pp.CaselessLiteral('response') + EQUAL + request_digest('response').setName('request-digest')
nonce =  pp.CaselessLiteral('nonce') + EQUAL + quoted_string('nonce')
realm =  pp.CaselessLiteral('realm') + EQUAL + quoted_string('realm')
username = pp.CaselessLiteral('username') + EQUAL + quoted_string('username')
dig_resp = username ^ realm ^ nonce ^ dresponse ^ digest_uri
digest_response = dig_resp + pp.ZeroOrMore(COMMA + dig_resp)
credentials = ((pp.CaselessLiteral('Digest') + pp.Suppress(LWS) + digest_response) ^ other_response)

Authorization = Parser(credentials)
def AuthorizationParse(headervalue):
    res = Authorization.parse(headervalue)
    scheme = res.pop(0)
    params = {}
    while res:
        k = res.pop(0)
        if res:
            res.pop(0)
            params[k] = res.pop(0)
    return {'auth-scheme':scheme, 'params':params}


#
#Authentication-Info  =  "Authentication-Info" HCOLON ainfo
#                        *(COMMA ainfo)
#ainfo                =  nextnonce / message-qop
#                         / response-auth / cnonce
#                         / nonce-count
#nextnonce            =  "nextnonce" EQUAL nonce-value
#response-auth        =  "rspauth" EQUAL response-digest
#response-digest      =  LDQUOT *LHEX RDQUOT
#
#Call-ID  =  ( "Call-ID" / "i" ) HCOLON callid
#callid   =  word [ "@" word ]
callid = word + pp.Optional(pp.Literal('@') + word)
Call_ID = Parser(callid)
def Call_IDParse(headervalue):
    res = Call_ID.parse(headervalue)
    callid = res.pop(0)
    return {'callid':callid}


#Call-Info   =  "Call-Info" HCOLON info *(COMMA info)
#info        =  LAQUOT absoluteURI RAQUOT *( SEMI info-param)
#info-param  =  ( "purpose" EQUAL ( "icon" / "info"
#               / "card" / token ) ) / generic-param
#
#Contact        =  ("Contact" / "m" ) HCOLON
#                  ( STAR / (contact-param *(COMMA contact-param)))
#contact-param  =  (name-addr / addr-spec) *(SEMI contact-params)
#name-addr      =  [ display-name ] LAQUOT addr-spec RAQUOT
#addr-spec      =  SIP-URI / SIPS-URI / absoluteURI !!! identical to Request-URI
#display-name   =  *(token LWS)/ quoted-string
#
#contact-params     =  c-p-q / c-p-expires
#                      / contact-extension
#c-p-q              =  "q" EQUAL qvalue
#c-p-expires        =  "expires" EQUAL delta-seconds
#contact-extension  =  generic-param
#delta-seconds      =  1*DIGIT
addr_spec = SIP_URI ^ SIPS_URI ^ absoluteURI
display_name = pp.Combine(pp.ZeroOrMore(token + LWS)) ^ quoted_string
name_addr = pp.Optional(display_name) + pp.Combine(LAQUOT + addr_spec + RAQUOT)

#Content-Disposition   =  "Content-Disposition" HCOLON
#                         disp-type *( SEMI disp-param )
#disp-type             =  "render" / "session" / "icon" / "alert"
#                         / disp-extension-token
#disp-param            =  handling-param / generic-param
#handling-param        =  "handling" EQUAL
#                         ( "optional" / "required"
#                         / other-handling )
#other-handling        =  token
#disp-extension-token  =  token
#
#Content-Encoding  =  ( "Content-Encoding" / "e" ) HCOLON
#                     content-coding *(COMMA content-coding)
#
#Content-Language  =  "Content-Language" HCOLON
#                     language-tag *(COMMA language-tag)
#language-tag      =  primary-tag *( "-" subtag )
#primary-tag       =  1*8ALPHA
#subtag            =  1*8ALPHA
#
#Content-Length  =  ( "Content-Length" / "l" ) HCOLON 1*DIGIT
Content_Length = Parser(pp.Word(pp.nums))
Content_LengthAlias = 'l'
def Content_LengthParse(headervalue):
    return dict(length=int(Content_Length.parse(headervalue)[0]))
def Content_LengthDisplay(cl):
    return "{}".format(cl.length)

#Content-Type     =  ( "Content-Type" / "c" ) HCOLON media-type
#media-type       =  m-type SLASH m-subtype *(SEMI m-parameter)
#m-type           =  discrete-type / composite-type
#discrete-type    =  "text" / "image" / "audio" / "video"
#                    / "application" / extension-token
#composite-type   =  "message" / "multipart" / extension-token
#extension-token  =  ietf-token / x-token
#ietf-token       =  token
#x-token          =  "x-" token
#m-subtype        =  extension-token / iana-token
#iana-token       =  token
#m-parameter      =  m-attribute EQUAL m-value
#m-attribute      =  token
#m-value          =  token / quoted-string
#
#CSeq  =  "CSeq" HCOLON 1*DIGIT LWS Method
CSeq = Parser(pp.Word(pp.nums) + pp.Suppress(LWS) + Method)
def CSeqParse(headervalue):
    res = CSeq.parse(headervalue)
    seq = int(res.pop(0))
    method = res.pop(0)
    return dict(seq=seq, method=method)

#Date          =  "Date" HCOLON SIP-date
#SIP-date      =  rfc1123-date
#rfc1123-date  =  wkday "," SP date1 SP time SP "GMT"
#date1         =  2DIGIT SP month SP 4DIGIT
#                 ; day month year (e.g., 02 Jun 1982)
#time          =  2DIGIT ":" 2DIGIT ":" 2DIGIT
#                 ; 00:00:00 - 23:59:59
#wkday         =  "Mon" / "Tue" / "Wed"
#                 / "Thu" / "Fri" / "Sat" / "Sun"
#month         =  "Jan" / "Feb" / "Mar" / "Apr"
#                 / "May" / "Jun" / "Jul" / "Aug"
#                 / "Sep" / "Oct" / "Nov" / "Dec"
#
#Error-Info  =  "Error-Info" HCOLON error-uri *(COMMA error-uri)
#error-uri   =  LAQUOT absoluteURI RAQUOT *( SEMI generic-param )
#
#Expires     =  "Expires" HCOLON delta-seconds
#From        =  ( "From" / "f" ) HCOLON from-spec
#from-spec   =  ( name-addr / addr-spec )
#               *( SEMI from-param )
#from-param  =  tag-param / generic-param
#tag-param   =  "tag" EQUAL token
#
#In-Reply-To  =  "In-Reply-To" HCOLON callid *(COMMA callid)
#
#Max-Forwards  =  "Max-Forwards" HCOLON 1*DIGIT
#
#MIME-Version  =  "MIME-Version" HCOLON 1*DIGIT "." 1*DIGIT
#
#Min-Expires  =  "Min-Expires" HCOLON delta-seconds
#
#Organization  =  "Organization" HCOLON [TEXT-UTF8-TRIM]
#
#Priority        =  "Priority" HCOLON priority-value
#priority-value  =  "emergency" / "urgent" / "normal"
#                   / "non-urgent" / other-priority
#other-priority  =  token
#
#Proxy-Authenticate  =  "Proxy-Authenticate" HCOLON challenge
#challenge           =  ("Digest" LWS digest-cln *(COMMA digest-cln))
#                       / other-challenge
#other-challenge     =  auth-scheme LWS auth-param
#                       *(COMMA auth-param)
#digest-cln          =  realm / domain / nonce
#                        / opaque / stale / algorithm
#                        / qop-options / auth-param
#realm               =  "realm" EQUAL realm-value
#realm-value         =  quoted-string
#domain              =  "domain" EQUAL LDQUOT URI
#                       *( 1*SP URI ) RDQUOT
#URI                 =  absoluteURI / abs-path
#nonce               =  "nonce" EQUAL nonce-value
#nonce-value         =  quoted-string
#opaque              =  "opaque" EQUAL quoted-string
#stale               =  "stale" EQUAL ( "true" / "false" )
#algorithm           =  "algorithm" EQUAL ( "MD5" / "MD5-sess"
#                       / token )
#qop-options         =  "qop" EQUAL LDQUOT qop-value
#                       *("," qop-value) RDQUOT
#qop-value           =  "auth" / "auth-int" / token

#Proxy-Authorization  =  "Proxy-Authorization" HCOLON credentials
Proxy_Authorization = credentials

#Proxy-Require  =  "Proxy-Require" HCOLON option-tag
#                  *(COMMA option-tag)
#option-tag     =  token
#
#Record-Route  =  "Record-Route" HCOLON rec-route *(COMMA rec-route)
#rec-route     =  name-addr *( SEMI rr-param )
#rr-param      =  generic-param
#
#Reply-To      =  "Reply-To" HCOLON rplyto-spec
#rplyto-spec   =  ( name-addr / addr-spec )
#                 *( SEMI rplyto-param )
#rplyto-param  =  generic-param
#Require       =  "Require" HCOLON option-tag *(COMMA option-tag)
#
#Retry-After  =  "Retry-After" HCOLON delta-seconds
#                [ comment ] *( SEMI retry-param )
#
#retry-param  =  ("duration" EQUAL delta-seconds)
#                / generic-param
#
#Route        =  "Route" HCOLON route-param *(COMMA route-param)
#route-param  =  name-addr *( SEMI rr-param )
rr_param = generic_param
route_param = name_addr + pp.ZeroOrMore(SEMI + rr_param)

Route = Parser(pp.Group(route_param) + pp.ZeroOrMore(pp.Group(COMMA + route_param)))
def RouteParse(headervalue):
    for res in Route.parse(headervalue):
        disp = res.pop(0)
        addr = res.pop(0)
        params = {}
        while res:
            k = res.pop(0)
            if res and res[0] == '=':
                res.pop(0)
                params[k] = res.pop(0)
            else:
                params[k] = None
        yield {'display-name':disp, 'addr-spec':addr, 'params':params}


    
#Server           =  "Server" HCOLON server-val *(LWS server-val)
#server-val       =  product / comment
#product          =  token [SLASH product-version]
#product-version  =  token
#
#Subject  =  ( "Subject" / "s" ) HCOLON [TEXT-UTF8-TRIM]
#
#Supported  =  ( "Supported" / "k" ) HCOLON
#              [option-tag *(COMMA option-tag)]
#
#Timestamp  =  "Timestamp" HCOLON 1*(DIGIT)
#               [ "." *(DIGIT) ] [ LWS delay ]
#delay      =  *(DIGIT) [ "." *(DIGIT) ]
#
#To        =  ( "To" / "t" ) HCOLON ( name-addr
#             / addr-spec ) *( SEMI to-param )
#to-param  =  tag-param / generic-param
#
#Unsupported  =  "Unsupported" HCOLON option-tag *(COMMA option-tag)
#User-Agent  =  "User-Agent" HCOLON server-val *(LWS server-val)

#Via               =  ( "Via" / "v" ) HCOLON via-parm *(COMMA via-parm)
#via-parm          =  sent-protocol LWS sent-by *( SEMI via-params )
#via-params        =  via-ttl / via-maddr
#                     / via-received / via-branch
#                     / via-extension
#via-ttl           =  "ttl" EQUAL ttl
#via-maddr         =  "maddr" EQUAL host
#via-received      =  "received" EQUAL (IPv4address / IPv6address)
#via-branch        =  "branch" EQUAL token
#via-extension     =  generic-param
#sent-protocol     =  protocol-name SLASH protocol-version
#                     SLASH transport
#protocol-name     =  "SIP" / token
#protocol-version  =  token
#transport         =  "UDP" / "TCP" / "TLS" / "SCTP"
#                     / other-transport
#sent-by           =  host [ COLON port ]
#ttl               =  1*3DIGIT ; 0 to 255
via_extension = generic_param
via_branch = pp.CaselessLiteral('branch') + EQUAL + token
via_received = pp.CaselessLiteral('received') + EQUAL + (IPv4address ^ IPv6address)
via_maddr = pp.CaselessLiteral('maddr') + EQUAL + host
ttl = pp.Word(pp.nums, max=3)
via_ttl = pp.CaselessLiteral('ttl') + EQUAL + ttl
via_params = via_ttl ^ via_maddr ^ via_received ^ via_branch ^ via_extension
sent_by = hostport =  pp.Combine(host + pp.Optional(COLON + pp.Word(pp.nums)))
transport = pp.CaselessLiteral('UDP') ^ pp.CaselessLiteral('TCP') ^ pp.CaselessLiteral('TLS') ^ pp.CaselessLiteral('SCTP') ^ other_transport
protocol_version = token
protocol_name = pp.CaselessLiteral('SIP') ^ token
sent_protocol = pp.Combine(protocol_name + SLASH + protocol_version + SLASH + transport)
via_parm = sent_protocol + pp.Suppress(LWS) + sent_by + pp.ZeroOrMore(SEMI + via_params)

Via = Parser(pp.Optional(pp.Group(via_parm) + pp.ZeroOrMore(pp.Group(COMMA + via_parm))))
ViaAlias = 'v'
def ViaParse(headervalue):
    for res in Via.parse(headervalue):
        protocol = res.pop(0)
        by = res.pop(0)
        params = {}
        while res:
            k = res.pop(0)
            if res and res[0] == '=':
                res.pop(0)
                params[k] = res.pop(0)
            else:
                params[k] = None
        yield {'sent_protocol':protocol, 'sent_by':by, 'params':params}
def ViaDisplay(via):
    params = (";{}{}".format(k, ("={}".format(v) if v is not None else "") or "") for k,v in via.params.items())
    return "{} {}{}".format(via.sent_protocol, via.sent_by, ''.join(params))

#
#Warning        =  "Warning" HCOLON warning-value *(COMMA warning-value)
#warning-value  =  warn-code SP warn-agent SP warn-text
#warn-code      =  3DIGIT
#warn-agent     =  hostport / pseudonym
#                  ;  the name or pseudonym of the server adding
#                  ;  the Warning header, for use in debugging
#warn-text      =  quoted-string
#pseudonym      =  token
#
#WWW-Authenticate  =  "WWW-Authenticate" HCOLON challenge
#
#extension-header  =  header-name HCOLON header-value
#header-name       =  token
#header-value      =  *(TEXT-UTF8char / UTF8-CONT / LWS)
#message-body  =  *OCTET
