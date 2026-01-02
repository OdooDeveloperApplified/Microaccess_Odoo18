from odoo import fields, models, api
import math

class SalesTemplate(models.Model):
    _inherit = "sale.order"

    # Custom fields added to Quotation form view of Sales module
    customer_status = fields.Selection([
        ('existingcustomer', 'Existing Customer'),
        ('newcustomer', 'New Customer'),
        ('dealer', 'Dealer'),
    ], string='Customer Status')
    subject = fields.Char(string="Subject")
    customer_po_no = fields.Char(string="Customer PO Number")
    customer_po_date = fields.Date(string="Customer PO Date")
    terms_id = fields.Many2one('terms.conditions', string="Terms & Conditions")
    expected_delivery_date = fields.Date(string="Expected Delivery Date")
    cancel_remarks = fields.Many2one('remarks.remarks', string="Cancel Remarks")
    remarks_cancel_ids = fields.Many2one('crm.lost.reason', string="Cancel Remarks New")
    
    partner_invoice_id = fields.Many2one(
        'res.partner',
        string="Invoice Address",
        compute="_compute_addresses_from_customer",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    partner_shipping_id = fields.Many2one(
        'res.partner',
        string="Delivery Address",
        compute="_compute_addresses_from_customer",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    partner_shipping_contact = fields.Char(related='partner_shipping_id.name', string = "Delivery Contact")
    partner_shipping_mobile= fields.Char(related='partner_shipping_id.mobile', string = "Delivery Mobile No.")

    @api.depends('partner_id')
    def _compute_addresses_from_customer(self):
        for rec in self:
            if rec.partner_id:
                addresses = rec.partner_id.address_get(['invoice', 'delivery'])
                rec.partner_invoice_id = addresses.get('invoice') or False
                rec.partner_shipping_id = addresses.get('delivery') or False

    @api.onchange('terms_id')
    def _onchange_terms_id(self):
        """ Auto-populate Terms & Conditions in the default 'note' field """
        if self.terms_id:
            self.note = self.terms_id.description  # Assign description to Odoo's default 'note' field
        else:
            self.note = ''
    
    # Custom fields added for Rounding-Off functionality

    is_enabled_roundoff = fields.Boolean(string="Apply Roundoff", default=False)
    amount_roundoff = fields.Monetary(string='Round-Off Amount', compute='_compute_amount_roundoff', store=True)
    amount_total_rounded = fields.Monetary(string='Total (Rounded)', compute='_compute_amount_roundoff', store=True)

    @api.depends('amount_total', 'currency_id', 'is_enabled_roundoff')
    def _compute_amount_roundoff(self):
        for order in self:
            if order.is_enabled_roundoff:
                floored_total = math.floor(order.amount_total)  # always rounds down
                order.amount_roundoff = floored_total - order.amount_total  # this will always be negative or 0
                order.amount_total_rounded = floored_total
            else:
                order.amount_roundoff = 0.0
                order.amount_total_rounded = order.amount_total


class SalesRemarks(models.Model):
    _name = "remarks.remarks"
    _description = "Sales Cancelled Remarks"
    _inherit=['mail.thread']
    _rec_name = "remarks"

    remarks = fields.Char(string="Sales Cancel Remarks")

class TermsConditions(models.Model):
    _name = 'terms.conditions'
    _description = 'Terms and Conditions' 
    _inherit=['mail.thread']
    

    name= fields.Char(string='Title', tracking=True)
    description = fields.Html(string = "Terms and Conditions")