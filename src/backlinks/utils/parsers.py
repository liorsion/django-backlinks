import sgmllib
import re
import htmlentitydefs
import urlparse


# make sgmllib behave better
sgmllib.tagfind = re.compile(r'[a-zA-Z][-_.:a-zA-Z0-9]*')
sgmllib.charref = re.compile(r'&#(?:([0-9]+)[^0-9])|(?:(x[0-9A-Fa-f]+)[^0-9A-Fa-f])')


class BaseParser(sgmllib.SGMLParser):
    """
    A more robust base markup parser.

    Fixes several common markup errors that cause SGMLParser to choke. Treats text
    enclosed in ``script`` and ``textarea`` as data. Normalizes entity references.

    """
    entity_or_charref = re.compile(r'&(?:'
      '([a-zA-Z][-.a-zA-Z0-9]*)|#(x?[0-9A-Fa-f]+)'
      ')(;?)')

    CODE_ENTITY_MAPPING = {
        '34': 'quot',
        '38': 'amp',
        '39': 'apos',
        '60': 'lt',
        '62': 'gt',
        'x22': 'quot',
        'x26': 'amp',
        'x27': 'apos',
        'x3c': 'lt',
        'x3e': 'gt',
    }

    MALFORMED_SELF_CLOSING_RE = re.compile('(<[^<>]*)/>')
    MALFORMED_COMMENT_RE = re.compile('<!\s+([^<>]*)>')
    
    def __init__(self, quote_tags=('script', 'textarea')):
        self.quote_tags = quote_tags
        sgmllib.SGMLParser.__init__(self)

    def reset(self):
        sgmllib.SGMLParser.reset(self)
        self.quote_tag_stack = []

    def feed(self, data):
        """
        Corrects several minor defects which can halt ``sgmllib.SGMLParser``.

        """
        self.rawdata = self.rawdata + data
        self.rawdata = self.MALFORMED_SELF_CLOSING_RE.sub(lambda x: x.group(1) + ' />', self.rawdata)
        self.rawdata = self.MALFORMED_COMMENT_RE.sub(lambda x: '<!' + x.group(1) + '>', self.rawdata)
        self.goahead(0)

    def unknown_starttag(self, tag, attrs):
        if tag in self.quote_tags:
            self.quote_tag_stack.append(tag)
            self.literal = True

    def unknown_endtag(self, tag):
        if self.quote_tag_stack and self.quote_tag_stack[-1] == tag:
            self.quote_tag_stack.pop()
            self.literal = (len(self.quote_tag_stack) > 0)

    def convert_codepoint(self, codepoint):
        return unichr(codepoint)

    def _convert_ref(self, match):
        if match.group(2):
            return self.convert_charref(match.group(2)) or \
                '&#%s%s' % match.groups()[1:]
        elif match.group(3):
            return self.convert_entityref(match.group(1)) or \
                '&%s;' % match.group(1)
        else:
            return '&%s' % match.group(1)


    def convert_charref(self, ref):
        ref = ref.lower()
        if ref in self.CODE_ENTITY_MAPPING:
            return '&%s;' % self.CODE_ENTITY_MAPPING[ref]
        else:
            if ref[0] == 'x':
                try:
                    n = int(ref[1:], 16)
                except ValueError:
                    return
            else:
                try:
                    n = int(ref)
                except ValueError:
                    return
        return self.convert_codepoint(n)

    def convert_entityref(self, ref):
        if ref in ('lt', 'gt', 'quot', 'amp', 'apos'):
            return '&%s;' % ref
        else:
            try:
                c = htmlentitydefs.name2codepoint[ref]
                return self.convert_codepoint(c)
            except KeyError:
                return


class LinkParser(BaseParser):
    """
    Parses out the value of the ``href`` attribute in all found ``a`` tags.

    """
    def __init__(self):
        BaseParser.__init__(self)

    def reset(self):
        BaseParser.reset(self)
        self.links = []

    def start_a(self, attrs):
        for k, v in attrs:
            if k.lower() == 'href':
                if v not in self.links:
                    self.links.append(v)

    def parse(self, doc):
        self.feed(doc)
        return self.links


class HttpLinkParser(LinkParser):
    """
    Parses out external ``href`` values in all found ``a`` tags.

    """
    def parse(self, doc):
        self.feed(doc)
        return filter(lambda url: url.lower().startswith('http://'), self.links)


class TitleParser(BaseParser):
    HEADING_TAGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    def reset(self):
        BaseParser.reset(self)
        self.in_title = False
        self.in_heading = False
        self.title = ''
        self.most_prominent_heading = [None, '']

    def start_title(self, attrs):
        self.in_title = True

    def end_title(self):
        self.in_title = False

    def unknown_starttag(self, tag, attrs):
        BaseParser.unknown_starttag(self, tag, attrs)
        if tag in self.HEADING_TAGS:
            level, contents = self.most_prominent_heading
            if not level or int(tag[1]) < int(level[1]):
                self.in_heading = True
                self.most_prominent_heading = [tag, '']

    def unknown_endtag(self, tag):
        BaseParser.unknown_endtag(self, tag)
        if tag in self.HEADING_TAGS:
            self.in_heading = False
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title = self.title + data
        elif self.in_heading:
            self.most_prominent_heading[1] = self.most_prominent_heading[1] + data

    def parse(self, data):
        self.feed(data)
        return self.title or (self.most_prominent_heading and self.most_prominent_heading[1]) or ''


class ContextualExcerptParser(BaseParser):
    """
    Parses out text in and around a linking anchor tag up to a given
    number of words.

    """
    def __init__(self):
        BaseParser.__init__(self)
    
    def reset(self):
        BaseParser.reset(self)
        self.parts = []
        self.target_url = None
        self.found_target_links = []
        self.in_target_link = False
        self.found_start_index = None

    def start_a(self, attrs):
        for k, v in attrs:
            if k.lower() == 'href':
                if v == self.target_url:
                    self.in_target_link = True
                    self.found_start_index = len(self.parts) - 1

    def end_a(self):
        if self.in_target_link:
            self.in_target_link = False
            self.found_target_links.append((self.found_start_index, len(self.parts) - 1))

    def handle_data(self, data):
        if not self.literal:
            self.parts.append(data)

    def parse(self, doc, target_url, max_words):
        """
        Sets up the parser and returns the built excerpt.

        """
        self.target_url = target_url
        self.feed(doc)
        return self.build_excerpts(max_words)

    def build_excerpts(self, max_words):
        """
        Returns a list of excerpts that are less than ``max_words`` in length.

        """
        import math
        parts = self.parts
        excerpts = []
        for start, end in self.found_target_links:
            split_words = []
            for segment in parts[start:end+1]:
                split_words.extend(segment.split())
                pieces = split_words
                initial_count = len(split_words)
                if initial_count > max_words:
                    pieces = split_words[:max_words]
                elif initial_count < max_words:
                    # gather pieces from neighbors
                    half_num_left = float(max_words - initial_count) / 2.0
                    num_left_words, num_right_words = int(math.ceil(half_num_left)), int(math.floor(half_num_left))
                    left_words, right_words = [], []
                    left_index, right_index = start, end
                    while len(left_words) < num_left_words:
                        left_index = left_index - 1
                        if left_index < 0:
                            num_right_words = num_right_words + (num_left_words - len(left_words))
                            break
                        left_pieces = parts[left_index].split()
                        if left_pieces:
                            lindex = min(len(left_pieces), num_left_words - len(left_words))
                            new_pieces = left_pieces[-lindex:]
                            new_pieces.extend(left_words)
                            left_words = new_pieces
                    while len(right_words) < num_right_words:
                        right_index = right_index + 1
                        if right_index >= len(parts):
                            break
                        right_pieces = parts[right_index].split()
                        if right_pieces:
                            rindex = min(len(right_pieces), num_right_words - len(right_words))
                            right_words.extend(right_pieces[:rindex])
                    pieces = left_words
                    pieces.extend(split_words)
                    pieces.extend(right_words)
            excerpts.append(' '.join(pieces))
        return excerpts
