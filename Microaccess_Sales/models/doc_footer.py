from odoo import api, fields, models

class BaseDocumentLayoutInherit(models.TransientModel):
    _inherit = 'base.document.layout'

    
    footer_image = fields.Binary(string="Footer Image",related='company_id.footer_image',readonly=False)

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    footer_image = fields.Binary(string="Footer Image")

# the above code is for relating the footer image uploaded in company form view which populates in configure document layout and vice-a-versa


