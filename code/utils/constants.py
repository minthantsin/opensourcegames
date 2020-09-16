"""
Paths, properties.
"""

import os
import configparser

# paths
root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
entries_path = os.path.join(root_path, 'entries')
tocs_path = os.path.join(entries_path, 'tocs')
code_path = os.path.join(root_path, 'code')
web_path = os.path.join(root_path, 'docs')
web_template_path = os.path.join(code_path, 'html')
web_css_path = os.path.join(web_path, 'css')


inspirations_file = os.path.join(root_path, 'inspirations.md')
developer_file = os.path.join(root_path, 'developers.md')

backlog_file = os.path.join(code_path, 'backlog.txt')
rejected_file = os.path.join(code_path, 'rejected.txt')
statistics_file = os.path.join(root_path, 'statistics.md')
json_db_file = os.path.join(root_path, 'docs', 'data.json')

# local config
local_config_file = os.path.join(root_path, 'local-config.ini')

config = configparser.ConfigParser()
config.read(local_config_file)


def get_config(key):
    """

    :param key:
    :return:
    """
    return config['general'][key]

# database entry constants
generic_comment_string = '[comment]: # (partly autogenerated content, edit with care, read the manual before)'

# these fields have to be present in each entry (in this order)
essential_fields = ('File', 'Title', 'Home', 'State', 'Keywords', 'Code repository', 'Code language', 'Code license')

valid_properties = ('Home', 'Media', 'Inspirations', 'State', 'Play', 'Download', 'Platform', 'Keywords', 'Code repository', 'Code language',
    'Code license', 'Code dependencies', 'Assets license', 'Developer')

# only these fields can be used currently (in this order)
valid_fields = ('File', 'Title') + valid_properties + ('Note', 'Building')

url_fields = ('Home', 'Media', 'Play', 'Download', 'Code repository')

valid_url_prefixes = ('http://', 'https://', 'git://', 'svn://', 'ftp://', 'bzr://')
extended_valid_url_prefixes = valid_url_prefixes + ('@see-', '@not-', '?')

valid_building_properties = ('Build system', 'Build instructions')
valid_building_fields = valid_building_properties + ('Note',)

# these are the only valid platforms currently (and must be given in this order)
valid_platforms = ('Windows', 'Linux', 'macOS', 'Android', 'iOS', 'Web')

# at least one of these must be used for every entry, this gives the principal categories and the order of the categories
recommended_keywords = (
    'action', 'arcade', 'adventure', 'visual novel', 'sports', 'platform', 'puzzle', 'role playing', 'simulation',
    'strategy', 'cards', 'board', 'music', 'educational', 'tool', 'game engine', 'framework', 'library', 'remake')

# known programming languages, anything else will result in a warning during a maintenance operation
# only these will be used when gathering statistics
known_languages = (
    'AGS Script', 'ActionScript', 'Ada', 'AngelScript', 'Assembly', 'Basic', 'Blender Script', 'BlitzMax', 'C', 'C#',
    'C++', 'Clojure', 'CoffeeScript', 'ColdFusion', 'D', 'DM', 'Dart', 'Dia', 'Elm', 'Emacs Lisp', 'F#', 'GDScript',
    'Game Maker Script', 'Go', 'Groovy', 'Haskell', 'Haxe', 'Io', 'Java', 'JavaScript', 'Kotlin', 'Lisp', 'Lua',
    'MegaGlest Script', 'MoonScript', 'None', 'OCaml', 'Objective-C', 'PHP', 'Pascal', 'Perl', 'Python', 'QuakeC', 'R',
    "Ren'Py", 'Ruby', 'Rust', 'Scala', 'Scheme', 'Script', 'Shell', 'Swift', 'TorqueScript', 'TypeScript', 'Vala',
    'Visual Basic', 'XUL', 'ZenScript', 'ooc', '?')

# known licenses, anything outside of this will result in a warning during a maintenance operation
# only these will be used when gathering statistics
known_licenses = (
    '2-clause BSD', '3-clause BSD', 'AFL-3.0', 'AGPL-3.0', 'Apache-2.0', 'Artistic License-1.0', 'Artistic License-2.0',
    'Boost-1.0', 'CC-BY-NC-3.0', 'CC-BY-NC-SA-2.0', 'CC-BY-NC-SA-3.0', 'CC-BY-SA-3.0', 'CC-BY-NC-SA-4.0',
    'CC-BY-SA-4.0', 'CC0', 'Custom', 'EPL-2.0', 'GPL-2.0', 'GPL-3.0', 'IJG', 'ISC', 'Java Research License', 'LGPL-2.0',
    'LGPL-2.1', 'LGPL-3.0', 'MAME', 'MIT', 'MPL-1.1', 'MPL-2.0', 'MS-PL', 'MS-RL', 'NetHack General Public License',
    'None', 'Proprietary', 'Public domain', 'SWIG license', 'Unlicense', 'WTFPL', 'wxWindows license', 'zlib', '?')

# valid multiplayer modes (can be combined with "+" )
valid_multiplayer_modes = (
    'competitive', 'co-op', 'hotseat', 'LAN', 'local', 'massive', 'matchmaking', 'online', 'split-screen')

# TODO put the abbreviations directly in the name line (parenthesis maybe), that is more natural
# this is a mapping of entry name to abbreviation and the abbreviations are used when specifying code dependencies
code_dependencies_aliases = {'Simple DirectMedia Layer': ('SDL', 'SDL2'), 'Simple and Fast Multimedia Library': ('SFML',),
                             'Boost (C++ Libraries)': ('Boost',), 'SGE Game Engine': ('SGE',), 'MegaGlest': ('MegaGlest Engine',)}

# these are code dependencies that won't get their own entry, because they are not centered on gaming
general_code_dependencies_without_entry = {'OpenGL': 'https://www.opengl.org/',
                                   'GLUT': 'https://www.opengl.org/resources/libraries/',
                                   'WebGL': 'https://www.khronos.org/webgl/',
                                   'Unity': 'https://unity.com/solutions/game',
                                   '.NET': 'https://dotnet.microsoft.com/', 'Vulkan': 'https://www.khronos.org/vulkan/',
                                   'KDE Frameworks': 'https://kde.org/products/frameworks/',
                                   'jQuery': 'https://jquery.com/',
                                   'node.js': 'https://nodejs.org/en/',
                                   'GNU Guile': 'https://www.gnu.org/software/guile/',
                                   'tkinter': 'https://docs.python.org/3/library/tk.html'}

# developer information (in the file all fields will be capitalized)
essential_developer_fields = ('Name', 'Games')
valid_developer_fields = essential_developer_fields + ('Contact', 'Home', 'Organization')
url_developer_fields = ('Home',)

# inspiration/original game information (in the file all fields will be capitalized)
essential_inspiration_fields = ('Name', 'Inspired entries')
valid_inspiration_fields = essential_inspiration_fields + ('Media',)
url_inspiration_fields = ('Media',)