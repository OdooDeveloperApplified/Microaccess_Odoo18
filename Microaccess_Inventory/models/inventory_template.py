from odoo import fields, models, api

class InventoryTemplate(models.Model):
    _inherit = "stock.picking"

    # Custom fields added to Tranfers form view of Inventory module
    is_return = fields.Boolean(string="Is Return")
    cus_po_no = fields.Char(string="Customer PO Number")
    cus_po_date = fields.Date(string="Customer PO Date")
    remarks = fields.Many2many('micro.remarks', string="Remarks")
    invoice_ids = fields.Many2many('account.move', string="Invoices", readonly=True)

    related_sale_order_id = fields.Many2one(
        'sale.order', string="Related Sale Order", compute='_compute_related_orders', store=False
    )
    related_purchase_order_id = fields.Many2one(
        'purchase.order', string="Related Purchase Order", compute='_compute_related_orders', store=False
    )
    related_order_button_label = fields.Char(string="Related Order Label", compute='_compute_related_orders', store=False)

    # Code to autopopulate customer PO related fields in tranfer types
    @api.model
    def create(self, vals):
        picking = super().create(vals)
        picking._set_customer_po_fields()
        return picking

    def _set_customer_po_fields(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing' and picking.origin:
                sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
                if sale_order:
                    picking.cus_po_no = sale_order.customer_po_no
                    picking.cus_po_date = sale_order.customer_po_date
    
    # Code to show the corresponding SO/PO on the receipts/delivery
    @api.depends('picking_type_id', 'origin')
    def _compute_related_orders(self):
        for picking in self:
            picking.related_sale_order_id = False
            picking.related_purchase_order_id = False
            picking.related_order_button_label = False

            if picking.origin:
                if picking.picking_type_id.code == 'outgoing':
                    picking.related_sale_order_id = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
                    picking.related_order_button_label = "Sale Order"
                elif picking.picking_type_id.code == 'incoming':
                    picking.related_purchase_order_id = self.env['purchase.order'].search([('name', '=', picking.origin)], limit=1)
                    picking.related_order_button_label = "Purchase Order"

    def action_open_related_order(self):
        self.ensure_one()
        if self.picking_type_id.code == 'outgoing' and self.related_sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Sale Order',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': self.related_sale_order_id.id,
                'target': 'current',
            }
        elif self.picking_type_id.code == 'incoming' and self.related_purchase_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Purchase Order',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'res_id': self.related_purchase_order_id.id,
                'target': 'current',
            }
        return False
    
   