from odoo import fields, models, api, _
from odoo.exceptions import UserError
class ContactsTemplate(models.Model):
    _inherit = "res.partner"

    # Custom fields added to Contacts form view
    contact_person = fields.Char(string='Contact First Name')
    surname = fields.Char(string='Contact Last Name')
    customer_support_email = fields.Char(string="Support Email")
    category_ids = fields.Many2one("category.master", string="Category")
    visiting_card_front = fields.Binary(string="Visiting Card Front")
    visiting_card_back = fields.Binary(string="Visiting Card Back")

    # Code for Daily call contact functionality
    is_lead_contact = fields.Boolean("Is Daily Call Contact", default=False)
    
    @api.model
    def create(self, vals):
        if self.env.context.get('from_lead'):
            vals['is_lead_contact'] = True
        if self.env.user.has_group('Microaccess_Contacts.no_contact_group'):
            raise UserError(_("Invalid operation: You are not allowed to create new Contacts."))
        else:
            return super(ContactsTemplate, self).create(vals)
        
    def write(self, vals):
        # Restrict editing contacts for specific users
        if self.env.user.has_group('Microaccess_Contacts.no_contact_group'):
        # Fields that are NOT allowed to be edited
            restricted_fields = {
                'name',
                'phone',
                'mobile',
                'email',
                'street',
                'street2',
                'city',
                'zip',
                'state_id',
                'country_id',
                'vat',
            }

            # If user tries to edit any restricted field → block
            if restricted_fields.intersection(vals.keys()):
                raise UserError(_("Invalid operation: You are not allowed to edit Contact details."))


        return super(ContactsTemplate, self).write(vals)
    
class CategoryMaster(models.Model):
    _name = "category.master"
    _description = "Category Master"
    _inherit = ['mail.thread']
    

    name = fields.Char(string="Name")

class product_template(models.Model):
    _inherit = "product.template"

    @api.model
    def create(self, vals):
        if self.env.user.has_group('Microaccess_Contacts.no_product_group'):
            raise UserError(_("Invalid operation: You are not allowed to create new Products."))
        else:
            return super(product_template, self).create(vals)
    
    def write(self, vals):
        # Block product editing
        if self.env.user.has_group('Microaccess_Contacts.no_product_group'):
            raise UserError(_("Invalid operation: You are not allowed to edit Product details."))

        return super(product_template, self).write(vals)


    