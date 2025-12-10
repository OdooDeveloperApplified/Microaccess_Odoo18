from odoo import fields, models, api

class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand' 
    _inherit=['mail.thread']
    _rec_name = 'brand_name'  

    brand_name= fields.Char(string='Brand Name', required=True, tracking=True)
    brand_description = fields.Text(string='Description', tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    product_count = fields.Integer(string="Product Count", compute="_compute_product_count")

    # Function to count the number of products linked to this brand
    @api.depends('brand_name')
    def _compute_product_count(self):
        for brand in self:
            brand.product_count = self.env['product.template'].search_count([('brand_id', '=', brand.id)])

    # Function to list all products linked to this brand
    def action_view_products(self):
        """Action to list all products linked to this brand, only if product_count > 0"""
        
        products = self.env['product.template'].search([('brand_id', '=', self.id)])
        if products:
            return {
                'name': 'Products',
                'type': 'ir.actions.act_window',
                'view_mode': 'list,form',
                'res_model': 'product.template',
                'domain': [('brand_id', '=', self.id)],
                'context': {'default_brand_id': self.id},
            }
       

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Field to link the product to the brand
    brand_id = fields.Many2one("product.brand", string="Brand", domain=[('active', '=', 'True')], help="Select a brand for this product.")
    is_service_product_for_e_invoicing = fields.Boolean(string="Is Service Product for e-Invoicing", default=False)
    allow_warranty = fields.Boolean(string="Allow Warranty", default=False)
    allow_warranty_renew = fields.Boolean(string="Allow Warranty Renew", default=False)
    warranty_period = fields.Integer(string="Warranty Period", default=0)
    period = fields.Selection([
        ('day', 'Day'),
        ('month', 'Month'),
        ('week', 'Week'),
        ('year', 'Year'),
    ], string='Period')
    warranty_type = fields.Selection([
        ('free', 'Free'),
        ('paid', 'Paid'),
    ], string='Warranty Type')

    auto_add_to_sale = fields.Boolean(string="Auto Add to Sale Order", help="If checked, this product will be automatically added to every new Sale Order.")

    
class ProductVariant(models.Model):
    _inherit = "product.product"

    # Field to link the product to the brand
    product_brand_id = fields.Many2one("product.brand", string="Brand", domain=[('active', '=', 'True')], help="Select a brand for this product.")
    
    