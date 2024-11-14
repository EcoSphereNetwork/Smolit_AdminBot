"""Version information for RootBot"""

__version__ = '0.2.0'
__author__ = 'RootBot Team'
__license__ = 'MIT'

VERSION_INFO = {
    'major': 0,
    'minor': 2,
    'patch': 0,
    'release': 'stable'
}

CHANGELOG = {
    '0.2.0': {
        'date': '2024-02-13',
        'changes': [
            'Added resource optimization and limits',
            'Enhanced error logging and monitoring',
            'Implemented alert system',
            'Added version management',
            'Improved documentation and examples'
        ]
    },
    '0.1.0': {
        'date': '2024-02-12',
        'changes': [
            'Initial release',
            'Basic system monitoring',
            'LLM integration',
            'Memory management'
        ]
    }
}

def get_version_info() -> dict:
    """Get detailed version information"""
    return {
        'version': __version__,
        'info': VERSION_INFO,
        'changelog': CHANGELOG
    }
