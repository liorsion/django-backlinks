VERSION = (0, 1, 'pre')
REVISION = '$Revision$'


def get_version():
    """Returns the human-readable version string."""
    version = '.'.join([str(i) for i in VERSION[:-1]])
    if VERSION[-1]:
        try:
            revision = REVISION.split()[1]
        except IndexError:
            revision = 'unknown'
        version = '%s-%s-rev%s' % (version, VERSION[-1], revision)
    return version
