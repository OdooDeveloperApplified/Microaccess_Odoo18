# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import http
from odoo.http import request
from odoo.osv.expression import AND


class CustomWebsiteHelpdesk(http.Controller):
    # Code to render smiley selection page on clicking 'provide your feedback' link
    @http.route(['/rate/<string:token>/select'], type='http', auth="public", website=True, sitemap=False)
    def custom_rating_select_page(self, token, **kwargs):
        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)], limit=1)
        if not rating:
            return request.not_found()

        return request.render('Microaccess_Helpdesk.custom_rating_selection_page', {
            'token': token,
            'rating': rating,
            'rate': rating.rating_text,
        })

    # Code to perform rating calculations (Used in built odoo rating controller code)
    @http.route(['/helpdesk/rating', '/helpdesk/rating/<model("helpdesk.team"):team>'], type='http', auth="public", website=True, sitemap=False)
    def page(self, team=False, **kw):
        # to avoid giving any access rights on helpdesk team to the public user, let's use sudo
        # and check if the user should be able to view the team (team managers only if it's not published or has no rating)
        user = request.env.user
        team_domain = [('id', '=', team.id)] if team else []
        if user.has_group('helpdesk.group_heldpesk_manager'):
            domain = AND([[('use_rating', '=', True)], team_domain])
        else:
            domain = AND([[('use_rating', '=', True), ('portal_show_rating', '=', True)], team_domain])
        teams = request.env['helpdesk.team'].search(domain)
        team_values = []
        for team in teams:
            tickets = request.env['helpdesk.ticket'].sudo().search([('team_id', '=', team.id)])
            domain = [
                ('res_model', '=', 'helpdesk.ticket'), ('res_id', 'in', tickets.ids),
                ('consumed', '=', True), ('rating', 'in', [1, 3, 4, 5]),
            ]
            ratings = request.env['rating.rating'].sudo().search(domain, order="id desc", limit=100)

            yesterday = (datetime.date.today()-datetime.timedelta(days=-1)).strftime('%Y-%m-%d 23:59:59')
            stats = {}
            any_rating = False
            for x in (7, 30, 90):
                todate = (datetime.date.today()-datetime.timedelta(days=x)).strftime('%Y-%m-%d 00:00:00')
                domdate = domain + [('create_date', '<=', yesterday), ('create_date', '>=', todate)]
                stats[x] = {1: 0, 3: 0, 4: 0, 5:0}
                rating_stats = request.env['rating.rating'].sudo()._read_group(domdate, ['rating'], ['__count'])
                total = sum(count for __, count in rating_stats)
                for rating, count in rating_stats:
                    any_rating = True
                    stats[x][rating] = (count * 100) / total
            values = {
                'team': team,
                'ratings': ratings if any_rating else False,
                'stats': stats,
                'is_helpdesk_user': user.has_group('helpdesk.group_helpdesk_user')
            }
            team_values.append(values)
        return request.render('helpdesk.team_rating_page', {'page_name': 'rating', 'teams': team_values})
    
    # Code to submit the feedback provided by customer on clicking 'Submit Feedback' button which reflects at the backend in Helpdesk module
    @http.route(['/rate/<string:token>/submit_feedback'], type='http', auth="public", website=True, csrf=True)
    def custom_rating_submit(self, token, **kwargs):
        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)], limit=1)
        if not rating:
            return request.not_found()

        # Custom label to value map
        rating_value_map = {
            'dissatisfied': 1,
            'ok': 3,
            'top': 4,
            'excellent': 5
        }

        rate_label = kwargs.get('rate')
        rate_value = rating_value_map.get(rate_label)
        feedback = kwargs.get('feedback')

        if not rate_value:
            return request.redirect('/rate/%s/select' % token)

        rating.write({
            'rating': rate_value,
            'feedback': feedback,
            'consumed': True,
        })

        if rating.res_model == 'helpdesk.ticket' and rating.res_id:
            ticket = request.env['helpdesk.ticket'].sudo().browse(rating.res_id)
            if ticket.exists():
                ticket.write({'feedback': feedback})

        # Code to move back to the homepage on clicking "Back to Homepage"
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

        return request.render('Microaccess_Helpdesk.rating_external_page_view', {
            'rating': rating,
            'web_base_url': base_url,
        })

