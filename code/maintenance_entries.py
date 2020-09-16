"""
Runs a series of maintenance operations on the collection of entry files, updating the table of content files for
each category as well as creating a statistics file.

Counts the number of records each sub-folder and updates the overview.
Sorts the entries in the contents files of each sub folder alphabetically.
"""

import os
import re
import datetime
import json
import textwrap
from utils import osg, osg_ui, utils, constants as c
import requests


def check_validity_backlog():
    import requests

    # read backlog and split
    file = os.path.join(c.root_path, 'code', 'backlog.txt')
    text = utils.read_text(file)
    urls = text.split('\n')
    urls = [x.split(' ')[0] for x in urls]

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=5)
        except Exception as e:
            print('{} gave error: {}'.format(url, e))
        else:
            if r.status_code != requests.codes.ok:
                print('{} returned status code: {}'.format(url, r.status_code))

            if r.is_redirect or r.history:
                print('{} redirected to {}, {}'.format(url, r.url, r.history))

def create_toc(title, file, entries):
    """

    """
    # file path
    toc_file = os.path.join(c.tocs_path, file)

    # header line
    text = '[comment]: # (autogenerated content, do not edit)\n# {}\n\n'.format(title)

    # assemble rows
    rows = []
    for entry in entries:
        info = entry['Code language'] + entry['Code license'] + entry['State']
        info = [x.value for x in info]
        rows.append('- **[{}]({})** ({})'.format(entry['Title'], '../' + entry['File'], ', '.join(info)))

    # sort rows (by title)
    rows.sort(key=str.casefold)

    # add to text
    text += '\n'.join(rows)

    # write to toc file
    utils.write_text(toc_file, text)


def sort_text_file(file, name):
    """
    Reads a text file, splits in lines, removes duplicates, sort, writes back.
    """
    text = utils.read_text(file)
    text = text.split('\n')
    text = sorted(list(set(text)), key=str.casefold)
    print('{} contains {} items'.format(name, len(text)))
    text = '\n'.join(text)
    utils.write_text(file, text)


class EntriesMaintainer:

    def __init__(self):
        self.entries = None

    def read_entries(self):
        self.entries = osg.read_entries()
        print('{} entries read'.format(len(self.entries)))

    def write_entries(self):
        if not self.entries:
            print('entries not yet loaded')
            return
        osg.write_entries(self.entries)
        print('entries written')


    def check_template_leftovers(self):
        """
        Checks for template leftovers.
        Should be run only occasionally.
        """
        # load template and get all lines
        text = utils.read_text(os.path.join(c.root_path, 'template.md'))
        text = text.split('\n')
        check_strings = [x for x in text if x and not x.startswith('##')]

        # iterate over all entries
        for _, entry_path, content in osg.entry_iterator():

            for check_string in check_strings:
                if content.find(check_string) >= 0:
                    print('{}: found {}'.format(os.path.basename(entry_path), check_string))
        print('checked for template leftovers')

    def check_inconsistencies(self):
        """

        :return:
        """
        if not self.entries:
            print('entries not yet loaded')
            return
        # get all keywords and print similar keywords
        keywords = []
        for entry in self.entries:
            keywords.extend(entry['Keywords'])
            if b'first\xe2\x80\x90person'.decode() in entry['Keywords']:
                print(entry['File'])
        keywords = [x.value for x in keywords]

        # reduce those starting with "multiplayer"
        keywords = [x if not x.startswith('multiplayer') else 'multiplayer' for x in keywords]

        # check unique keywords
        unique_keywords = list(set(keywords))
        unique_keywords_counts = [keywords.count(l) for l in unique_keywords]
        for index, name in enumerate(unique_keywords):
            for other_index in range(index+1, len(unique_keywords)):
                other_name = unique_keywords[other_index]
                if osg.name_similarity(name, other_name) > 0.8:
                    print(' Keywords {} ({}) - {} ({}) are similar'.format(name, unique_keywords_counts[index], other_name, unique_keywords_counts[other_index]))

        # get all names of frameworks and library also using osg.code_dependencies_aliases
        valid_dependencies = list(c.general_code_dependencies_without_entry.keys())
        for entry in self.entries:
            if any((x in ('framework', 'library', 'game engine') for x in entry['Keywords'])):
                name = entry['Title']
                if name in c.code_dependencies_aliases:
                    valid_dependencies.extend(c.code_dependencies_aliases[name])
                else:
                    valid_dependencies.append(name)

        # get all referenced code dependencies
        referenced_dependencies = {}
        for entry in self.entries:
            deps = entry.get('Code dependencies', [])
            for dependency in deps:
                dependency = dependency.value
                if dependency in referenced_dependencies:
                    referenced_dependencies[dependency] += 1
                else:
                    referenced_dependencies[dependency] = 1

        # delete those that are valid dependencies
        referenced_dependencies = [(k, v) for k, v in referenced_dependencies.items() if k not in valid_dependencies]

        # sort by number
        referenced_dependencies.sort(key=lambda x: x[1], reverse=True)

        # print out
        print('Code dependencies not included as entry')
        for dep in referenced_dependencies:
            print('{} ({})'.format(*dep))

        # if there is the "Play" field, it should have "Web" as Platform
        for entry in self.entries:
            name = entry['File']
            if 'Play' in entry:
                if not 'Platform' in entry:
                    print('Entry "{}" has "Play" field but not "Platform" field, add it with "Web"'.format(name))
                elif not 'Web' in entry['Platform']:
                    print('Entry "{}" has "Play" field but not "Web" in "Platform" field'.format(name))
        # javascript/typescript as language but not web as platform?

        # if there is a @see-download there should be download fields...

    def clean_rejected(self):
        """

        :return:
        """
        # sort rejected games list file
        sort_text_file(os.path.join(c.root_path, 'code', 'rejected.txt'), 'rejected games list')

    def clean_backlog(self):
        """

        :return:
        """
        if not self.entries:
            print('entries not yet loaded')
            return
        # get urls from entries
        included_urls = osg.all_urls(self.entries)
        included_urls = list(included_urls.keys())  # only need the URLs here

        # get urls from rejected file
        text = utils.read_text(c.rejected_file)
        regex = re.compile(r"\((http.*?)\)", re.MULTILINE)
        matches = regex.findall(text)
        rejected_urls = []
        for match in matches:
            urls = match.split(',')
            urls = [x.strip() for x in urls]
            rejected_urls.extend(urls)
        included_urls.extend(rejected_urls)

        # those that only have a web archive version, also get the original version
        more_urls = []
        for url in included_urls:
            if url.startswith('https://web.archive.org/web'):
                # print(url) # sometimes the http is missing in archive links (would need proper parsing)
                url = url[url.index('http', 5):]
                more_urls.append(url)
        included_urls.extend(more_urls)

        # now we strip the urls
        stripped_urls = [utils.strip_url(x) for x in included_urls]
        stripped_urls = set(stripped_urls)  # removes duplicates for performance

        # read backlog and get urls from there
        text = utils.read_text(c.backlog_file)
        text = text.split('\n')

        # remove those that are in stripped_game_urls
        text = [x for x in text if utils.strip_url(x) not in stripped_urls]

        # remove duplicates and sort
        text = sorted(list(set(text)), key=str.casefold)
        print('backlog contains {} items'.format(len(text)))

        # join and save again
        text = '\n'.join(text)
        utils.write_text(c.backlog_file, text)

        print('backlog cleaned')

    def check_external_links(self):
        """
        Checks all external links it can find for validity. Prints those with non OK HTTP responses. Does only need to be run
        from time to time.
        """

        # regex for finding urls (can be in <> or in ]() or after a whitespace
        regex = re.compile(r"[\s\n]<(http.+?)>|\]\((http.+?)\)|[\s\n](http[^\s\n,]+?)[\s\n\)]")

        # ignore the following patterns (they give false positives here)
        ignored_urls = (
        'https://git.tukaani.org/xz.git', 'https://git.code.sf.net/', 'http://hg.hedgewars.org/hedgewars/',
        'https://git.xiph.org/vorbis.git', 'http://svn.uktrainsim.com/svn/openrails', 'https://www.srb2.org/',
        'http://wiki.srb2.org/')

        # some do redirect, but we nedertheless want the original URL in the database
        redirect_okay = ('https://octaforge.org/', 'https://svn.openttd.org/', 'https://godotengine.org/download')

        # extract all links from entries
        import urllib3
        urllib3.disable_warnings()  # otherwise we cannot verify those with SSL errors without getting warnings
        urls = {}
        for entry, _, content in osg.entry_iterator():
            # apply regex
            matches = regex.findall(content)
            # for each match
            for match in matches:
                for url in match:
                    if url and not any((url.startswith(x) for x in ignored_urls)):
                        # ignore bzr.sourceforge, no web address found
                        if 'bzr.sourceforge.net/bzrroot/' in url:
                            continue

                        # add "/" at the end
                        if any((url.startswith(x) for x in (
                        'https://anongit.freedesktop.org/git', 'https://git.savannah.gnu.org/git/',
                        'https://git.savannah.nongnu.org/git/', 'https://git.artsoft.org/'))):
                            url += '/'

                        if url.startswith('https://bitbucket.org/') and url.endswith('.git'):
                            url = url[:-4] + '/commits/'
                        if url.startswith('https://svn.code.sf.net/p/'):
                            url = 'http' + url[5:] + '/'
                        if url.startswith('http://cvs.savannah.nongnu.org:/sources/'):
                            url = 'http://cvs.savannah.nongnu.org/viewvc/' + url[40:] + '/'
                        if url.startswith('http://cvs.savannah.gnu.org:/sources/'):
                            url = 'http://cvs.savannah.gnu.org/viewvc/' + url[37:] + '/'

                        # generally ".git" at the end is not working well, except sometimes
                        if url.endswith('.git') and not any((url.startswith(x) for x in (
                        'https://repo.or.cz', 'https://git.tuxfamily.org/fanwor/fanwor'))):
                            url = url[:-4]

                        if url in urls:
                            urls[url].add(entry)
                        else:
                            urls[url] = {entry}
        print('found {} unique links'.format(len(urls)))
        print("start checking external links (can take a while)")

        # now iterate over all urls
        for url, names in urls.items():
            names = list(names)  # was a set
            if len(names) == 1:
                names = names[0]
            try:
                verify = True
                # some have an expired certificate but otherwise still work
                if any((url.startswith(x) for x in (
                'https://perso.b2b2c.ca/~sarrazip/dev/', 'https://dreerally.com/', 'https://henlin.net/',
                'https://www.megamek.org/', 'https://pixeldoctrine.com/', 'https://gitorious.org/',
                'https://www.opmon-game.ga/'))):
                    verify = False
                r = requests.head(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'}, timeout=20,
                                  allow_redirects=True, verify=verify)
                if r.status_code == 405:  # head method not supported, try get
                    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64)'},
                                     timeout=20, allow_redirects=True, verify=verify)
                # check for bad status
                if r.status_code != requests.codes.ok:
                    print('{}: {} - {}'.format(names, url, r.status_code))
                # check for redirect
                if r.history and url not in redirect_okay:
                    # only / added or http->https sometimes
                    redirected_url = r.url
                    if redirected_url == url + '/':
                        output = '{}: {} -> {} - redirect "/" at end '
                    elif redirected_url == 'https' + url[4:]:
                        output = '{}: {} -> {} - redirect "https" at start'
                    else:
                        output = '{}: {} -> {} - redirect '
                    print(output.format(names, url, redirected_url))
            except Exception as e:
                error_name = type(e).__name__
                if error_name == 'SSLError' and any((url.startswith(x) for x in (
                'https://gitorious.org/', 'https://www.freedroid.org/download/'))):
                    continue  # even though verify is False, these errors still get through
                print('{}: {} - exception {}'.format(names, url, error_name))

    def update_readme_tocs(self):
        """
        Recounts entries in sub categories and writes them to the readme.
        Also updates the _toc files in the categories directories.

        Note: The Readme must have a specific structure at the beginning, starting with "# Open Source Games" and ending
        on "A collection.."

        Needs to be performed regularly.
        """

        # completely delete content of toc path
        for file in os.listdir(c.tocs_path):
            os.remove(os.path.join(c.tocs_path, file))

        # read readme
        readme_file = os.path.join(c.root_path, 'README.md')
        readme_text = utils.read_text(readme_file)

        # compile regex for identifying the building blocks in the readme
        regex = re.compile(r"(.*?)(\[comment\]: # \(start.*?end of autogenerated content\))(.*)", re.DOTALL)

        # apply regex
        matches = regex.findall(readme_text)
        if len(matches) != 1:
            raise RuntimeError('readme file has invalid structure')
        matches = matches[0]
        start = matches[0]
        end = matches[2]

        tocs_text = ''

        # split into games, tools, frameworks, libraries
        games = [x for x in self.entries if not any([y in x['Keywords'] for y in ('tool', 'framework', 'library')])]
        tools = [x for x in self.entries if 'tool' in x['Keywords']]
        frameworks = [x for x in self.entries if 'framework' in x['Keywords']]
        libraries = [x for x in self.entries if 'library' in x['Keywords']]
        
        # create games, tools, frameworks, libraries tocs
        title = 'Games'
        file = '_games.md'
        tocs_text += '**[{}](entries/tocs/{}#{})** ({}) - '.format(title, file, title, len(games))
        create_toc(title, file, games)

        title = 'Tools'
        file = '_tools.md'
        tocs_text += '**[{}](entries/tocs/{}#{})** ({}) - '.format(title, file, title, len(tools))
        create_toc(title, file, tools)

        title = 'Frameworks'
        file = '_frameworks.md'
        tocs_text += '**[{}](entries/tocs/{}#{})** ({}) - '.format(title, file, title, len(frameworks))
        create_toc(title, file, frameworks)

        title = 'Libraries'
        file = '_libraries.md'
        tocs_text += '**[{}](entries/tocs/{}#{})** ({})\n'.format(title, file, title, len(libraries))
        create_toc(title, file, libraries)

        # create by category
        categories_text = []
        for keyword in c.recommended_keywords:
            filtered = [x for x in self.entries if keyword in x['Keywords']]
            title = keyword.capitalize()
            name = keyword.replace(' ', '-')
            file = '_{}.md'.format(name)
            categories_text.append('**[{}](entries/tocs/{}#{})** ({})'.format(title, file, name, len(filtered)))
            create_toc(title, file, filtered)
        categories_text.sort()
        tocs_text += '\nBy category: {}\n'.format(', '.join(categories_text))

        # create by platform
        platforms_text = []
        for platform in c.valid_platforms:
            filtered = [x for x in self.entries if platform in x.get('Platform', [])]
            title = platform
            name = platform.lower()
            file = '_{}.md'.format(name)
            platforms_text.append('**[{}](entries/tocs/{}#{})** ({})'.format(title, file, name, len(filtered)))
            create_toc(title, file, filtered)
        tocs_text += '\nBy platform: {}\n'.format(', '.join(platforms_text))

        # insert new text in the middle (the \n before the second comment is necessary, otherwise Markdown displays it as part of the bullet list)
        text = start + "[comment]: # (start of autogenerated content, do not edit)\n" + tocs_text + "\n[comment]: # (end of autogenerated content)" + end

        # write to readme
        utils.write_text(readme_file, text)

        print('Readme and TOCs updated')

    def update_statistics(self):
        """
        Generates the statistics page.

        Should be done every time the entries change.
        """
        if not self.entries:
            print('entries not yet loaded')
            return

        # start the page
        statistics = '[comment]: # (autogenerated content, do not edit)\n# Statistics\n\n'

        # total number
        number_entries = len(self.entries)
        rel = lambda x: x / number_entries * 100  # conversion to percent

        statistics += 'analyzed {} entries on {}\n\n'.format(number_entries,
                                                             datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # State (beta, mature, inactive)
        statistics += '## State\n\n'

        number_state_beta = sum(1 for x in self.entries if 'beta' in x['State'])
        number_state_mature = sum(1 for x in self.entries if 'mature' in x['State'])
        number_inactive = sum(1 for x in self.entries if osg.is_inactive(x))
        statistics += '- mature: {} ({:.1f}%)\n- beta: {} ({:.1f}%)\n- inactive: {} ({:.1f}%)\n\n'.format(
            number_state_mature, rel(number_state_mature), number_state_beta, rel(number_state_beta), number_inactive,
            rel(number_inactive))

        if number_inactive > 0:
            entries_inactive = [(x['Title'], osg.extract_inactive_year(x)) for x in self.entries if osg.is_inactive(x)]
            entries_inactive.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
            entries_inactive.sort(key=lambda x: x[1], reverse=True)  # then sort by inactive year (more recently first)
            entries_inactive = ['{} ({})'.format(*x) for x in entries_inactive]
            statistics += '##### Inactive State\n\n' + ', '.join(entries_inactive) + '\n\n'

        # Language
        statistics += '## Code Languages\n\n'
        field = 'Code language'

        # get all languages together
        languages = []
        for entry in self.entries:
            languages.extend(entry[field])
        languages = [x.value for x in languages]

        unique_languages = set(languages)
        unique_languages = [(l, languages.count(l) / len(languages)) for l in unique_languages]
        unique_languages.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
        unique_languages.sort(key=lambda x: x[1], reverse=True)  # then sort by occurrence (highest occurrence first)
        unique_languages = ['- {} ({:.1f}%)\n'.format(x[0], x[1] * 100) for x in unique_languages]
        statistics += '##### Language frequency\n\n' + ''.join(unique_languages) + '\n'

        # Licenses
        statistics += '## Code licenses\n\n'
        field = 'Code license'

        # get all licenses together
        licenses = []
        for entry in self.entries:
            licenses.extend(entry[field])
        licenses = [x.value for x in licenses]

        unique_licenses = set(licenses)
        unique_licenses = [(l, licenses.count(l) / len(licenses)) for l in unique_licenses]
        unique_licenses.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
        unique_licenses.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)
        unique_licenses = ['- {} ({:.1f}%)\n'.format(x[0], x[1] * 100) for x in unique_licenses]
        statistics += '##### Licenses frequency\n\n' + ''.join(unique_licenses) + '\n'

        # Keywords
        statistics += '## Keywords\n\n'
        field = 'Keywords'

        # get all keywords together
        keywords = []
        for entry in self.entries:
            keywords.extend(entry[field])
        keywords = [x.value for x in keywords]

        # reduce those starting with "multiplayer"
        keywords = [x if not x.startswith('multiplayer') else 'multiplayer' for x in keywords]

        unique_keywords = set(keywords)
        unique_keywords = [(l, keywords.count(l) / len(keywords)) for l in unique_keywords]
        unique_keywords.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
        unique_keywords.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)
        unique_keywords = ['- {} ({:.1f}%)'.format(x[0], x[1] * 100) for x in unique_keywords]
        statistics += '##### Keywords frequency\n\n' + '\n'.join(unique_keywords) + '\n\n'

        # no download or play field
        statistics += '## Entries without download or play fields\n\n'

        entries = []
        for entry in self.entries:
            if 'Download' not in entry and 'Play' not in entry:
                entries.append(entry['Title'])
        entries.sort(key=str.casefold)
        statistics += '{}: '.format(len(entries)) + ', '.join(entries) + '\n\n'

        # code hosted not on github, gitlab, bitbucket, launchpad, sourceforge
        popular_code_repositories = ('github.com', 'gitlab.com', 'bitbucket.org', 'code.sf.net', 'code.launchpad.net')
        statistics += '## Entries with a code repository not on a popular site\n\n'

        entries = []
        field = 'Code repository'
        for entry in self.entries:
            popular = False
            for repo in entry[field]:
                for popular_repo in popular_code_repositories:
                    if popular_repo in repo.value:
                        popular = True
                        break
            # if there were repositories, but none popular, add them to the list
            if not popular:
                entries.append(entry['Title'])
                # print(info[field])
        entries.sort(key=str.casefold)
        statistics += '{}: '.format(len(entries)) + ', '.join(entries) + '\n\n'

        # Code dependencies
        statistics += '## Code dependencies\n\n'
        field = 'Code dependencies'

        # get all code dependencies together
        code_dependencies = []
        entries_with_code_dependency = 0
        for entry in self.entries:
            if field in entry:
                code_dependencies.extend(entry[field])
                entries_with_code_dependency += 1
        code_dependencies = [x.value for x in code_dependencies]
        statistics += 'With code dependency field {} ({:.1f}%)\n\n'.format(entries_with_code_dependency,
                                                                           rel(entries_with_code_dependency))

        unique_code_dependencies = set(code_dependencies)
        unique_code_dependencies = [(l, code_dependencies.count(l) / len(code_dependencies)) for l in
                                    unique_code_dependencies]
        unique_code_dependencies.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
        unique_code_dependencies.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)
        unique_code_dependencies = ['- {} ({:.1f}%)'.format(x[0], x[1] * 100) for x in unique_code_dependencies]
        statistics += '##### Code dependencies frequency\n\n' + '\n'.join(unique_code_dependencies) + '\n\n'

        # Build systems:
        statistics += '## Build systems\n\n'
        field = 'Build system'

        # get all build systems together
        build_systems = []
        for entry in self.entries:
            if field in entry['Building']:
                build_systems.extend(entry['Building'][field])
        build_systems = [x.value for x in build_systems]

        statistics += 'Build systems information available for {:.1f}% of all projects.\n\n'.format(
            rel(len(build_systems)))

        unique_build_systems = set(build_systems)
        unique_build_systems = [(l, build_systems.count(l) / len(build_systems)) for l in unique_build_systems]
        unique_build_systems.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
        unique_build_systems.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)
        unique_build_systems = ['- {} ({:.1f}%)'.format(x[0], x[1] * 100) for x in unique_build_systems]
        statistics += '##### Build systems frequency ({})\n\n'.format(len(build_systems)) + '\n'.join(
            unique_build_systems) + '\n\n'

        # C, C++ projects without build system information
        c_cpp_project_without_build_system = []
        for entry in self.entries:
            if field not in entry and ('C' in entry['Code language'] or 'C++' in entry['Code language']):
                c_cpp_project_without_build_system.append(entry['Title'])
        c_cpp_project_without_build_system.sort(key=str.casefold)
        statistics += '##### C and C++ projects without build system information ({})\n\n'.format(
            len(c_cpp_project_without_build_system)) + ', '.join(c_cpp_project_without_build_system) + '\n\n'

        # C, C++ projects with build system information but without CMake as build system
        c_cpp_project_not_cmake = []
        for entry in entries:
            if field in entry and 'CMake' in entry[field] and (
                    'C' in entry['Code language'] or 'C++' in entry['Code language']):
                c_cpp_project_not_cmake.append(entry['Title'])
        c_cpp_project_not_cmake.sort(key=str.casefold)
        statistics += '##### C and C++ projects with a build system different from CMake ({})\n\n'.format(
            len(c_cpp_project_not_cmake)) + ', '.join(c_cpp_project_not_cmake) + '\n\n'

        # Platform
        statistics += '## Platform\n\n'
        field = 'Platform'

        # get all platforms together
        platforms = []
        for entry in self.entries:
            if field in entry:
                platforms.extend(entry[field])
        platforms = [x.value for x in platforms]

        statistics += 'Platform information available for {:.1f}% of all projects.\n\n'.format(rel(len(platforms)))

        unique_platforms = set(platforms)
        unique_platforms = [(l, platforms.count(l) / len(platforms)) for l in unique_platforms]
        unique_platforms.sort(key=lambda x: str.casefold(x[0]))  # first sort by name
        unique_platforms.sort(key=lambda x: -x[1])  # then sort by occurrence (highest occurrence first)
        unique_platforms = ['- {} ({:.1f}%)'.format(x[0], x[1] * 100) for x in unique_platforms]
        statistics += '##### Platforms frequency\n\n' + '\n'.join(unique_platforms) + '\n\n'

        # write to statistics file
        utils.write_text(c.statistics_file, statistics)

        print('statistics updated')

    def update_html(self):
        """
        Parses all entries, collects interesting info and stores it in a json file suitable for displaying
        with a dynamic table in a browser.
        """
        if not self.entries:
            print('entries not yet loaded')
            return

        # make database out of it
        db = {'headings': ['Game', 'Description', 'Download', 'State', 'Keywords', 'Source']}

        entries = []
        for info in self.entries:

            # game & description
            entry = ['{} (<a href="{}">home</a>, <a href="{}">entry</a>)'.format(info['Title'], info['Home'][0],
                                                                                 r'https://github.com/Trilarion/opensourcegames/blob/master/entries/' +
                                                                                 info['File']),
                     textwrap.shorten(info.get('Note', ''), width=60, placeholder='..')]

            # download
            field = 'Download'
            if field in info and info[field]:
                entry.append('<a href="{}">Link</a>'.format(info[field][0]))
            else:
                entry.append('')

            # state (field state is essential)
            entry.append('{} / {}'.format(info['State'][0],
                                          'inactive since {}'.format(osg.extract_inactive_year(info)) if osg.is_inactive(info) else 'active'))

            # keywords
            keywords = info['Keywords']
            keywords = [x.value for x in keywords]
            entry.append(', '.join(keywords))

            # source
            text = []
            field = 'Code repository'
            if field in info and info[field]:
                text.append('<a href="{}">Source</a>'.format(info[field][0].value))
            languages = info['Code language']
            languages = [x.value for x in languages]
            text.append(', '.join(languages))
            licenses = info['Code license']
            licenses = [x.value for x in licenses]
            text.append(', '.join(licenses))
            entry.append(' - '.join(text))

            # append to entries
            entries.append(entry)

        # sort entries by game name
        entries.sort(key=lambda x: str.casefold(x[0]))

        db['data'] = entries

        # output
        text = json.dumps(db, indent=1)
        utils.write_text(c.json_db_file, text)

        print('HTML updated')

    def update_repos(self):
        """
        export to json for local repository update of primary repos
        """
        if not self.entries:
            print('entries not yet loaded')
            return

        primary_repos = {'git': [], 'svn': [], 'hg': []}
        unconsumed_entries = []

        # for every entry filter those that are known git repositories (add additional repositories)
        for entry in self.entries:
            repos = entry['Code repository']
            repos = [x.value for x in repos]
            # keep the first and all others containing @add
            if not repos:
                continue
            repos = [repos[0]] + [x for x in repos[1:] if "@add" in x]
            for repo in repos:
                consumed = False
                repo = repo.split(' ')[0].strip()
                url = osg.git_repo(repo)
                if url:
                    primary_repos['git'].append(url)
                    consumed = True
                    continue
                url = osg.svn_repo(repo)
                if url:
                    primary_repos['svn'].append(url)
                    consumed = True
                    continue
                url = osg.hg_repo(repo)
                if url:
                    primary_repos['hg'].append(url)
                    consumed = True
                    continue

                if not consumed:
                    unconsumed_entries.append([entry['Title'], repo])
                    print('Entry "{}" unconsumed repo: {}'.format(entry['File'], repo))

        # sort them alphabetically (and remove duplicates)
        for k, v in primary_repos.items():
            primary_repos[k] = sorted(set(v))

        # statistics of gits
        git_repos = primary_repos['git']
        print('{} Git repositories'.format(len(git_repos)))
        for domain in (
                'repo.or.cz', 'anongit.kde.org', 'bitbucket.org', 'git.code.sf.net', 'git.savannah', 'git.tuxfamily',
                'github.com',
                'gitlab.com', 'gitlab.com/osgames', 'gitlab.gnome.org'):
            print('{} on {}'.format(sum(1 if domain in x else 0 for x in git_repos), domain))

        # write them to code/git
        json_path = os.path.join(c.root_path, 'code', 'archives.json')
        text = json.dumps(primary_repos, indent=1)
        utils.write_text(json_path, text)

        print('Repositories updated')

    def collect_git_repos(self):
        """
        for every entry, get all git
        :return:
        """

        git_repos = []
        for entry in self.entries:
            repos = entry['Code repository']
            repos = [x.value for x in repos]
            for repo in repos:
                repo = repo.split(' ')[0].strip()
                url = osg.git_repo(repo)
                if url:
                    git_repos.append(repo)

        # sort them alphabetically (and remove duplicates)
        git_repos = sorted(list(set(git_repos)), key=str.casefold)

        # write them to code/git
        json_path = os.path.join(c.root_path, 'code', 'git_repositories.json')
        text = json.dumps(git_repos, indent=1)
        utils.write_text(json_path, text)

    def special_ops(self):
        """
        For special operations that are one-time and may change.
        :return:
        """
        if not self.entries:
            print('entries not yet loaded')
            return
        # remove all downloads that only have a single entry with @see-home (this is the default anyway)
        field = 'Download'
        for entry in self.entries:
            if field in entry:
                content = entry[field]
                if len(content) == 1 and content[0].value == '@see-home' and not content[0].comment:
                    del entry[field]
        print('special ops finished')

    def complete_run(self):
        pass


if __name__ == "__main__":

    m = EntriesMaintainer()

    actions = {
        'Read entries': m.read_entries,
        'Write entries': m.write_entries,
        'Check template leftovers': m.check_template_leftovers,
        'Check inconsistencies': m.check_inconsistencies,
        'Check rejected entries': m.clean_rejected,
        'Check external links (takes quite long)': m.check_external_links,
        'Clean backlog': m.clean_backlog,
        'Update Readme and TOCs': m.update_readme_tocs,
        'Update statistics': m.update_statistics,
        'Update HTML': m.update_html,
        'Update repository list': m.update_repos,
        'Special': m.special_ops,
        'Complete run': m.complete_run
    }

    osg_ui.run_simple_button_app('Entries developer', actions)


