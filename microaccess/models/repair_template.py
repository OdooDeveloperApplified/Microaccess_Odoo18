from odoo import fields, models, api

class RepairTemplate(models.Model):
    _inherit = "repair.order"

    # Custom fields added to Repair form view of Helpdesk module
    warranty_expiration_date = fields.Date(string="Warranty Expiration")
    subject = fields.Char(string="Subject")
    invoice_method = fields.Selection([
        ('no_invoice', 'No Invoice'),
        ('before_repair', 'Before Repair'),
        ('after_repair', 'After Repair'),
    ], string="Invoice Method")
    remarks_ids = fields.Many2many('micro.remarks', string="Remarks")
    remarks_description = fields.Text(string="Remarks & Description")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket No.")
    partner_name = fields.Char(related="partner_id.name", string="Partner Name")

class RepairTag(models.Model):
    _name = "repair.tag"
    _description = "Repair Tags"
    _inherit = ['mail.thread']

    name = fields.Char(string="Tag Name")
   