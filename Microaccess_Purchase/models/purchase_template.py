from odoo import fields, models, api, _
import math
from odoo.exceptions import UserError


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
    other_address_reports = fields.Many2one('res.partner', string="Other Address")
    purchase_sale_order2 = fields.Many2many("sale.order", string="Sale Order No.") 
    is_enabled_roundoff = fields.Boolean(string="Apply Roundoff", default=True)
    purchase_repair_order = fields.Many2many('repair.order', string="Repair Order No.")
    amount_roundoff = fields.Monetary(string='Round-Off Amount', compute='_compute_amount_roundoff', store=True)
    amount_total_rounded = fields.Monetary(string='Total (Rounded)', compute='_compute_amount_roundoff', store=True)

    @api.depends('amount_total', 'currency_id', 'is_enabled_roundoff')
    def _compute_amount_roundoff(self):
        for order in self:
            if order.is_enabled_roundoff:
                # Round using standard rounding (>=0.5 up, <0.5 down)
                rounded_total = round(order.amount_total)
                order.amount_roundoff = rounded_total - order.amount_total
                order.amount_total_rounded = rounded_total
            else:
                order.amount_roundoff = 0.0
                order.amount_total_rounded = order.amount_total

    # Code to auto-populate the products tab based on the selected sale order(s) in the RFQ form view
    @api.onchange('purchase_sale_order2', 'purchase_repair_order')
    def _onchange_purchase_sale_order2(self):
        """
        Auto-populate the products tab based on the selected sale order(s)/repair order(s).
        """
        self.order_line = [(5, 0, 0)]  # Clear existing order lines
        order_lines = []
        
        for sale_order in self.purchase_sale_order2:
            for line in sale_order.order_line:
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'taxes_id': line.tax_id.ids,
                    'price_subtotal': line.price_subtotal,
                }))
        # ----------- From Repair Orders -----------
        for repair_order in self.purchase_repair_order:
            for line in repair_order.move_ids:
                # Get taxes either from the repair line (if present) or from the product
                taxes = False
                if hasattr(line, 'tax_id') and line.tax_id:
                    taxes = [(6, 0, line.tax_id.ids)]
                elif line.product_id and line.product_id.supplier_taxes_id:
                    taxes = [(6, 0, line.product_id.supplier_taxes_id.ids)]

                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty or 1.0,
                    'product_uom': (
                        line.product_uom_id.id
                        if hasattr(line, 'product_uom_id')
                        else line.product_uom.id
                    ),
                    'price_unit': line.price_unit or 0.0,
                    'taxes_id': taxes,
                }))

        
        self.order_line = order_lines
        
    # Code to auto populate the T&C saved in purchase > settings > default terms and conditions in RFQ/PO form view    
    @api.model
    def create(self, vals):
        if not vals.get('notes'):
            enable_terms = self.env['ir.config_parameter'].sudo().get_param('purchase.is_default_purchase_terms')
            if enable_terms == 'True':
                default_terms = self.env['ir.config_parameter'].sudo().get_param('purchase.default_terms_conditions')
                default_terms_html = default_terms.replace('\n', '<br/>').replace('\\n', '<br/>')
                vals['notes'] = default_terms_html
        return super(PurchaseTemplate, self).create(vals)
    
    ##################### Remove this code after data import: start #####################
    # Removed default=fields.Datetime.now
    # date_order = fields.Datetime(
    #     string='Order Deadline',
    #     required=True,
    #     index=True,
    #     copy=False,
    #     help="Depicts the date within which the Quotation should be confirmed and converted into a purchase order."
    # )

    # date_approve = fields.Datetime(
    #     string='Confirmation Date',
    #     readonly=True,
    #     index=True,
    #     copy=False,
    #     help="Date when the purchase order was approved."
    # )

    # def button_approve(self, force=False):
    #     """Custom approve button — skip auto updating date_approve"""
    #     self = self.filtered(lambda order: order._approval_allowed())

    #     # Ensure date_order is always set for receipt generation
    #     for order in self:
    #         if not order.date_order:
    #             order.date_order = fields.Datetime.now()

    #     # Approve the order
    #     self.write({'state': 'purchase'})

    #     # Handle company PO lock if configured
    #     self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
    #     return {}

    
    ##################### Remove this code after data import: end #####################

    
    def unlink(self):
        if self.env.user.has_group('Microaccess_Purchase.group_hide_delete_button'):
            raise UserError(_("Invalid operation: You are not allowed to delete Purchase Orders."))
        return super(PurchaseTemplate, self).unlink()

class ResCompany(models.Model):
    _inherit = 'res.company'

    stamp = fields.Binary("Stamp Image", attachment=True)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_default_purchase_terms = fields.Boolean(
        string="Default Terms and Conditions",
        config_parameter='purchase.is_default_purchase_terms'
    )

    purchase_terms_conditions = fields.Char(
        string="Default Purchase Terms and Conditions",
        config_parameter='purchase.default_terms_conditions',
    )




