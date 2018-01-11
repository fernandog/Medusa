Manual search for:<br>
    <a href="home/displayShow?indexername=${show.indexer_name}&seriesid=${series.series_id}" class="snatchTitle">${series.name}</a> / Season ${season}
        % if manual_search_type != 'season':
            Episode ${episode}
        % endif
    </a>
