# This code is based on the class ``UnicodeDammit`` from BeautifulSoup, which
# was written by Leonard Richardson.

import codecs
import types
import re
try:
    import chardet
    CHARDET_INSTALLED = True
except ImportError:
    CHARDET_INSTALLED = False

# see
#   http://www.mozilla.org/quality/intl/intl_data/testpages.html
#   http://www.mozilla.org/quality/intl/browser/charsethandling/testcase-CharsetHandlingI.html


BOM_ENCODING_MAP = (
    ('\xef\xbb\xbf', 'utf-8'),
    ('\xff\xfe\0\0', 'utf-32'),
    ('\0\0\xfe\xff', 'UTF-32BE'),
    ('\xff\xfe', 'utf-16'),
    ('\xfe\xff', 'UTF-16BE'),
)

MS_CHARS = {
    u'\x80' : ('euro', '20AC'),
    u'\x81' : ' ',
    u'\x82' : ('sbquo', '201A'),
    u'\x83' : ('fnof', '192'),
    u'\x84' : ('bdquo', '201E'),
    u'\x85' : ('hellip', '2026'),
    u'\x86' : ('dagger', '2020'),
    u'\x87' : ('Dagger', '2021'),
    u'\x88' : ('circ', '2C6'),
    u'\x89' : ('permil', '2030'),
    u'\x8A' : ('Scaron', '160'),
    u'\x8B' : ('lsaquo', '2039'),
    u'\x8C' : ('OElig', '152'),
    u'\x8D' : '?',
    u'\x8E' : ('#x17D', '17D'),
    u'\x8F' : '?',
    u'\x90' : '?',
    u'\x91' : ('lsquo', '2018'),
    u'\x92' : ('rsquo', '2019'),
    u'\x93' : ('ldquo', '201C'),
    u'\x94' : ('rdquo', '201D'),
    u'\x95' : ('bull', '2022'),
    u'\x96' : ('ndash', '2013'),
    u'\x97' : ('mdash', '2014'),
    u'\x98' : ('tilde', '2DC'),
    u'\x99' : ('trade', '2122'),
    u'\x9a' : ('scaron', '161'),
    u'\x9b' : ('rsaquo', '203A'),
    u'\x9c' : ('oelig', '153'),
    u'\x9d' : '?',
    u'\x9e' : ('#x17E', '17E'),
    u'\x9f' : ('Yuml', ''),
}

class Unicodifier(object):
    """
    A simple utility class which attempts to convert a *ML document to a unicode
    string.

    """
    def __init__(self, document):
        self.document = document
        self.original_encoding = ''

    def convert(self, proposed_encodings=[], quotes_to='html', errors='strict'):
        # Short circuit if we're already unicode
        if self.document == '' or isinstance(self.document, unicode):
            return unicode(self.document)

        converted_document = None

        # Check for BOM, if exists, strip it and convert the document
        for bom, encoding in BOM_ENCODING_MAP:
            if self.document.startswith(bom):
                try:
                    converted_document = unicode(self.document[len(bom):],
                                                 encoding,
                                                 errors='strict')
                    self.original_encoding = encoding
                except UnicodeDecodeError:
                    pass

        # Try proposed encodings
        if not converted_document and proposed_encodings:
            for encoding in proposed_encodings:
                try:
                    converted_document = self._convert(encoding, errors='strict')
                    if converted_document:
                        break
                except UnicodeDecodeError:
                    pass

        # If not already unicode and not encoded in the proposed encodings,
        # try to sniff encoding with chardet, or try the most common encodings
        if not converted_document:
            if CHARDET_INSTALLED:
                try:
                    possible_encoding = chardet.detect(self.document)['encoding']
                    converted_document = self._convert(possible_encoding, errors='strict')
                except UnicodeDecodeError:
                    pass
            # fallback if no chardet or chardet's guess was wrong
            if not converted_document: 
                for possible_encoding in ('utf-8', 'iso-8859-1', 'windows-1252'):
                    try:
                        converted_document = self._convert(possible_encoding, errors=errors)
                        if converted_document:
                            break
                    except UnicodeDecodeError:
                        continue

        # check for windows encoding, substitute ms chars if applicable
        if quotes_to and self.original_encoding.lower() in ('windows-1252',
                                                            'iso-8859-1',
                                                            'iso-8859-2'):
            converted_document = re.compile(r'([\x80-\x9f])').sub \
                                    (lambda(x): self._convert_mschar(x.group(1), quotes_to),
                                     converted_document)

        return converted_document

    def get_codec(self, charset):
        return self._codec(charset) \
            or (charset and self._codec(charset.replace('-', ''))) \
            or (charset and self._codec(charset.replace('-', '_'))) \
            or charset

    def _codec(self, charset):
        if not charset:
            return charset
        codec = None
        try:
            codec = codecs.lookup(charset)
            codec = charset
        except (LookupError, ValueError):
            pass
        return codec

    def _convert(self, encoding, errors='strict'):
        codec = self.get_codec(encoding)
        try:
            converted_document = unicode(self.document, codec, errors=errors)
            self.original_encoding = encoding
        except ValueError:
            converted_document = u''
        return converted_document

    def _convert_mschar(self, original, quotes_to):
        substitute = MS_CHARS.get(original)
        if substitute and type(substitute) == types.TupleType:
            if quotes_to == 'xml':
                substitute = u'&#x%s;' % substitute[1]
            else:
                substitute = u'&%s;' % substitute[0]
        return substitute

def unicodify(document, proposed_encodings=[]):
    unicodifier = Unicodifier(document)
    return unicodifier.convert(proposed_encodings), unicodifier.original_encoding
