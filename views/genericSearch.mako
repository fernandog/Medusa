<%inherit file="/layouts/main.mako"/>
<%!
    from medusa import app
    from medusa.helpers import pretty_file_size
%>
<%block name="scripts">
</%block>
<%block name="content">
<div class="clearfix"></div><!-- div.clearfix //-->

<div class="row">
    <div class="col-md-6"> <!-- Title -->
        % if not header is UNDEFINED:
            <h1 class="header">${header}</h1>
        % else:
            <h1 class="title">${title}</h1>
        % endif
    </div> <!-- layout title -->
    <div class="col-md-12">
        <div class="clearfix"></div><!-- .clearfix //-->
        <div id="wrapper" data-history-toggle="hide">
            <div id="container">
            <table class="defaultTable tablesorter" cellspacing="1" border="0" cellpadding="0">
                <thead>
                    <tr>
                        <th>Provider</th>
                        <th>Title</th>
                        <th>Seeders</th>
                        <th>Leechers</th>
                        <th>Size</th>
                    </tr>
                </thead>
                <tfoot>
                    <tr>
                        <th class="nowrap" colspan="5">&nbsp;</th>
                    </tr>
                </tfoot>
                <tbody>
                % for provider_image, items in results:
                    % for item in items:
                            <tr>
                            <td align="center">
                                <img src="images/providers/${provider_image}" width="16" height="16" style="vertical-align:middle;" />
                            </td>
                            <td>
                                <a href="${item.get('link')}">${item.get('title')}</a>
                            </td>
                            <td align="center">
                                ${item.get('seeders')}
                            </td>
                            <td align="center">
                                ${item.get('leechers')}
                            </td>
                            <td align="center">
                                ${pretty_file_size(item.get('size'))}
                            </td>
                            </tr>
                    % endfor
                % endfor
                </tbody>
            </table>
            </div><!-- #container //-->
        </div><!-- #wrapper //-->
    </div><!-- col -->
</div><!-- row -->
</%block>
