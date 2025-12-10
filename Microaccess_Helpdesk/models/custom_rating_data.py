# -*- coding: utf-8 -*-
# rating_override.py
from odoo import fields, models, api
import operator
from odoo.addons.rating.models import rating_data
from odoo.tools.float_utils import float_compare

# Override rating constants
rating_data.RATING_TEXT = [
    ('excellent', 'Excellent'),
    ('top', 'Satisfied'),
    ('ok', 'Okay'),
    ('ko', 'Dissatisfied'),
    ('none', 'No Rating yet'),
]

# Optional thresholds
rating_data.RATING_LIMIT_EXCELLENT = 5
rating_data.RATING_LIMIT_SATISFIED = 4
rating_data.RATING_LIMIT_OK = 3
rating_data.RATING_LIMIT_MIN = 1
rating_data.RATING_AVG_EXCELLENT = 4.9 
rating_data.RATING_AVG_TOP = 3.66
rating_data.RATING_AVG_OK = 2.33
rating_data.RATING_AVG_MIN = 1

# Override _rating_to_text
def _custom_rating_to_text(rating_value):
    rating_data._rating_assert_value(rating_value)
    if rating_value == 5:
        return 'excellent'
    if rating_value >= rating_data.RATING_LIMIT_SATISFIED:
        return 'top'
    if rating_value >= rating_data.RATING_LIMIT_OK:
        return 'ok'
    if rating_value >= rating_data.RATING_LIMIT_MIN:
        return 'ko'
    return 'none'

# Override _rating_avg_to_text
def _custom_rating_avg_to_text(rating_avg):
    if float_compare(rating_avg, rating_data.RATING_AVG_EXCELLENT, 2) >= 0:
        return 'excellent'
    if float_compare(rating_avg, rating_data.RATING_AVG_TOP, 2) >= 0:
        return 'top'
    if float_compare(rating_avg, rating_data.RATING_AVG_OK, 2) >= 0:
        return 'ok'
    if float_compare(rating_avg, rating_data.RATING_AVG_MIN, 2) >= 0:
        return 'ko'
    return 'none'

# Patch them into Odoo
rating_data._rating_to_text = _custom_rating_to_text
rating_data._rating_avg_to_text = _custom_rating_avg_to_text


class RatingRating(models.Model):
    _inherit = 'rating.rating'

    rating_text = fields.Selection(
        selection_add=[('excellent', 'Excellent')],
        compute='_compute_rating_text_custom',
        store=True
    )

    @api.depends('rating')
    def _compute_rating_text_custom(self):
        for rec in self:
            if rec.rating == 5:
                rec.rating_text = 'excellent'
            else:
                rec.rating_text = rating_data._rating_to_text(rec.rating)
                
