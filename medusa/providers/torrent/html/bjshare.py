# coding=utf-8

"""Provider code for BJ-Share."""

from __future__ import unicode_literals

import logging
import re

from medusa import tv
from medusa.bs4_parser import BS4Parser
from medusa.helper.common import convert_size, try_int
from medusa.logger.adapters.style import BraceAdapter
from medusa.providers.torrent.torrent_provider import TorrentProvider

from requests.compat import urljoin

log = BraceAdapter(logging.getLogger(__name__))
log.logger.addHandler(logging.NullHandler())


class BJShareProvider(TorrentProvider):
    """BJ-Share Torrent provider."""

    def __init__(self):
        """Initialize the class."""
        super(BJShareProvider, self).__init__('BJ-Share')

        # URLs
        self.url = 'https://bj-share.info'
        self.urls = {
            'search': urljoin(self.url, 'torrents.php')
        }

        # Credentials
        self.enable_cookies = True
        self.cookies = ''
        self.required_cookies = ['session']

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # Miscellaneous Options
        self.supports_absolute_numbering = True
        self.max_back_pages = 2

        # Proper Strings
        self.proper_strings = ['PROPER', 'REPACK', 'REAL', 'RERIP']

        # Cache
        self.cache = tv.Cache(self, min_time=30)

        # One piece is the only anime that i'm aware that is in "absolute" numbering, the problem is that they include
        # the season (wrong season) and episode as absolute, eg: One Piece - S08E836
        # 836 is the latest episode in absolute numbering, that is correct, but S08 is not the current season...
        # So for this show, i don't see a other way to make it work...
        #
        # All others animes that i tested is with correct season and episode set, so i can't remove the season from all
        # or will break everything else
        #
        # In this indexer, it looks that it is added "automatically", so all current and new releases will be broken
        # until they or the source from where they get that info fix it...
        self.absolute_numbering = [
            'One Piece'
        ]

    def search(self, search_strings, age=0, ep_obj=None, **kwargs):
        """
        Search a provider and parse the results.

        :param search_strings: A dict with mode (key) and the search value (value)
        :param age: Not used
        :param ep_obj: Informations about the episode being searched (when not RSS)

        :returns: A list of search results (structure)
        """
        results = []
        if not self.login():
            return results

        manual_search = kwargs.get('manual_search')
        if manual_search:
            self.max_back_pages = 20

        anime = False
        if ep_obj and ep_obj.series:
            anime = ep_obj.series.anime == 1

        search_params = {
            'order_by': 'time',
            'order_way': 'desc',
            'group_results': 0,
            'action': 'basic',
            'searchsubmit': 1
        }

        if 'RSS' in search_strings.keys():
            search_params['filter_cat[14]'] = 1  # anime
            search_params['filter_cat[2]'] = 1  # tv shows
        elif anime:
            search_params['filter_cat[14]'] = 1  # anime
        else:
            search_params['filter_cat[2]'] = 1  # tv shows

        for mode in search_strings:
            items = []
            log.debug(u'Search Mode: {0}'.format(mode))

            # if looking for season, look for more pages
            if mode == 'Season' and not manual_search:
                self.max_back_pages = 10

            for search_string in search_strings[mode]:
                if mode != 'RSS':
                    log.debug(u'Search string: {0}'.format(search_string.decode('utf-8')))

                # Remove season / episode from search (not supported by tracker)
                search_str = re.sub(r'\d+$' if anime else r'[S|E]\d\d', '', search_string).strip()
                search_params['searchstr'] = search_str
                next_page = 1
                has_next_page = True

                while has_next_page and next_page <= self.max_back_pages:
                    search_params['page'] = next_page
                    log.debug(u'Page Search: {0}'.format(next_page))
                    next_page += 1

                    response = self.session.get(self.urls['search'], params=search_params)
                    if not response:
                        log.debug('No data returned from provider')
                        continue

                    result = self._parse(response.content, mode)
                    has_next_page = result['has_next_page']
                    items += result['items']

                results += items

        return results

    def _parse(self, data, mode):
        """
        Parse search results for items.

        :param data: The raw response from a search
        :param mode: The current mode used to search, e.g. RSS

        :return: A KV with a list of items found and if there's an next page to search
        """
        def process_column_header(td):
            ret = u''
            if td.a and td.a.img:
                ret = td.a.img.get('title', td.a.get_text(strip=True))
            if not ret:
                ret = td.get_text(strip=True)
            return ret

        items = []
        has_next_page = False
        with BS4Parser(data, 'html5lib') as html:
            torrent_table = html.find('table', id='torrent_table')
            torrent_rows = torrent_table('tr') if torrent_table else []

            # ignore next page in RSS mode
            has_next_page = mode != 'RSS' and html.find('a', class_='pager_next') is not None
            log.debug(u'More Pages? {0}'.format(has_next_page))

            # Continue only if at least one Release is found
            if len(torrent_rows) < 2:
                log.debug('Data returned from provider does not contain any torrents')
                return {'has_next_page': has_next_page, 'items': []}

            # '', '', 'Name /Year', 'Files', 'Time', 'Size', 'Snatches', 'Seeders', 'Leechers'
            labels = [process_column_header(label) for label in torrent_rows[0]('td')]
            group_title = u''

            # Skip column headers
            for result in torrent_rows[1:]:
                cells = result('td')
                result_class = result.get('class')
                # When "Grouping Torrents" is enabled, the structure of table change
                group_index = -2 if 'group_torrent' in result_class else 0
                try:
                    title = result.select('a[href^="torrents.php?id="]')[0].get_text()
                    title = re.sub('\s+', ' ', title).strip()  # clean empty lines and multiple spaces

                    if 'group' in result_class or 'torrent' in result_class:
                        # get international title if available
                        title = re.sub('.* \[(.*?)\](.*)', r'\1\2', title)

                    if 'group' in result_class:
                        group_title = title
                        continue

                    for serie in self.absolute_numbering:
                        if serie in title:
                            # remove season from title when its in absolute format
                            title = re.sub('S\d{2}(E\d{2,4})', r'\1', title)
                            break

                    download_url = urljoin(self.url, result.select('a[href^="torrents.php?action=download"]')[0]['href'])
                    if not all([title, download_url]):
                        continue

                    seeders = try_int(cells[labels.index('Seeders') + group_index].get_text(strip=True))
                    leechers = try_int(cells[labels.index('Leechers') + group_index].get_text(strip=True))

                    # Filter unseeded torrent
                    if seeders < min(self.minseed, 1):
                        if mode != 'RSS':
                            log.debug("Discarding torrent because it doesn't meet the"
                                      ' minimum seeders: {0}. Seeders: {1}',
                                      title, seeders)
                        continue

                    torrent_details = None
                    if 'group_torrent' in result_class:
                        # torrents belonging to a group
                        torrent_details = title
                        title = group_title
                    elif 'torrent' in result_class:
                        # standalone/un grouped torrents
                        torrent_details = cells[labels.index('Nome/Ano')].find('div', class_='torrent_info').get_text()

                    torrent_details = torrent_details.replace('[', ' ').replace(']', ' ').replace('/', ' ')
                    torrent_details = torrent_details.replace('Full HD ', '1080p').replace('HD ', '720p')

                    torrent_size = cells[labels.index('Tamanho')+group_index].get_text(strip=True)
                    size = convert_size(torrent_size) or -1

                    torrent_name = '{0} {1}'.format(title, torrent_details.strip()).strip()
                    torrent_name = re.sub('\s+', ' ', torrent_name)

                    items.append({
                        'title': torrent_name,
                        'link': download_url,
                        'size': size,
                        'seeders': seeders,
                        'leechers': leechers,
                        'pubdate': None
                    })

                    if mode != 'RSS':
                        log.debug('Found result: {0} with {1} seeders and {2} leechers'.format
                                  (torrent_name, seeders, leechers))

                except (AttributeError, TypeError, KeyError, ValueError, IndexError):
                    log.exception('Failed parsing provider.')

        return {'has_next_page': has_next_page, 'items': items}

    def login(self):
        """Login method used for logging in before doing a search and torrent downloads."""
        return self.cookie_login('Login', check_url=self.urls['search'])


provider = BJShareProvider()
