from odoo import fields, models, api

class ContactsTemplate(models.Model):
    _inherit = "res.partner"

    # Custom fields added to Contacts form view
    contact_person = fields.Char(string='Contact Person')
    customer_support_email = fields.Char(string="Support Email")
    category_ids = fields.Many2one("category.master", string="Category")
    
class CategoryMaster(models.Model):
    _name = "category.master"
    _description = "Category Master"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name")
    