def _get_user_agent_string():
    from backlinks import get_version
    return "Django Backlinks %s" % get_version()

INSTALLED_MODULES = [
    ('pingback', 'Pingback', 'backlinks.pingback.client.default_client'),
    ('trackback', 'TrackBack', 'backlinks.trackback.client.default_client'),
]

MAX_EXCERPT_WORDS = 32
MAX_URL_READ_LENGTH = 8192
USER_AGENT_STRING = _get_user_agent_string
