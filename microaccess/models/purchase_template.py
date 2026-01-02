from odoo import fields, models, api


class PurchaseTemplate(models.Model):
    _inherit = "purchase.order"

    # Custom fields added to RFQ form view of Purchase module
    against_selection = fields.Selection([
        ('against_stock', 'Against Stock'),
        ('against_order', 'Against Order'),
    ], string='Against Order',required=True, default='against_stock')
    shipping_address = fields.Selection([
        ('micro', 'Micro Access'),
        ('order', 'Order'),
    ], string='Shipping Address',required=True, default='micro')
    purchase_sale_order2 = fields.Many2many("sale.order", string="Sale Order No.") 
    is_enabled_roundoff = fields.Boolean(string="Apply Roundoff")
    purchase_repair_order = fields.Many2many('repair.order', string="Repair Order No.")

    # Code to auto-populate the products tab based on the selected sale order(s) in the RFQ form view
    @api.onchange('purchase_sale_order2')
    def _onchange_purchase_sale_order2(self):
        """
        Auto-populate the products tab based on the selected sale order(s).
        """
        self.order_line = [(5, 0, 0)]  # Clear existing order lines
        order_lines = []
        
        for sale_order in self.purchase_sale_order2:
            for line in sale_order.order_line:
                order_lines.append((0, 0, {
                    'product_id': line.product_template_id.id,
                    'name': line.name,
                    'product_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'taxes_id': line.tax_id.ids,
                    'price_subtotal': line.price_subtotal,
                }))
        
        self.order_line = order_lines
