from odoo import fields, models, api

class InventoryTemplate(models.Model):
    _inherit = "stock.picking"

    # Custom fields added to Tranfers form view of Inventory module
    is_return = fields.Boolean(string="Is Return")
    cus_po_no = fields.Char(string="Customer PO Number")
    cus_po_date = fields.Date(string="Customer PO Date")
    remarks = fields.Many2many('micro.remarks', string="Remarks")
    invoice_ids = fields.Many2many('account.move', string="Invoices", readonly=True)
   