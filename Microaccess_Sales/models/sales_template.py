from odoo import fields, models, api, _
from odoo.exceptions import UserError
import math
import logging
_logger = logging.getLogger(__name__)


class SalesTemplate(models.Model):
    _inherit = "sale.order"

    # Custom fields added to Quotation form view of Sales module
    customer_status = fields.Selection([
        ('existingcustomer', 'Existing Customer'),
        ('newcustomer', 'New Customer'),
        ('dealer', 'Dealer'),
    ], string='Customer Status')
    subject = fields.Char(string="Subject")
    customer_po_no = fields.Char(string="Customer PO No.")
    customer_po_date = fields.Date(string="Customer PO Date")
    terms_id = fields.Many2one('terms.conditions', string="Terms & Conditions", default=2)
    expected_delivery_date = fields.Date(string="Expected Delivery Date")
    cancel_remarks = fields.Many2one('remarks.remarks', string="Cancel Remarks")
    remarks_cancel_ids = fields.Many2one('crm.lost.reason', string="Cancel Remarks New")
    partner_invoice_id = fields.Many2one(
        'res.partner',
        string="Invoice Address",
        compute="_compute_addresses_from_customer",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    # Old delivery address code
    partner_shipping_id = fields.Many2one(
        'res.partner',
        string="Delivery Address",
        compute="_compute_addresses_from_customer",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    partner_shipping = fields.Char(string="Delivery Address")

    partner_shipping_contact = fields.Char(string = "Delivery Contact")
    partner_shipping_mobile= fields.Char(string = "Delivery Mobile No.")

    revision_ids = fields.One2many('revision.history', 'sale_id', string='Revision History')
    revision_date = fields.Date(string="Revision Date", compute="_compute_latest_revision_date", store=True)
    amc_terms_name = fields.Char(related="terms_id.name", store=True)

    billing_period = fields.Selection([
        ('monthly', 'Monthly'),
        ('quaterly', 'Quaterly'),
        ('half yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
    ], string='Billing Period')

    amc_type = fields.Selection([
        ('comprehensive', 'Comprehensive'),
        ('non-comprehensive', 'Non-comprehensive'),
    ], string='AMC Type')

    amc_start_date = fields.Date(string="AMC Start Date")
    amc_end_date = fields.Date(string="AMC End Date")


    # Remove this code after data import over: start#
    date_order = fields.Datetime(
        string="Order Date",
        required=True, copy=False,
        help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    # Remove this code after data import over: start#

    @api.depends('revision_ids.revision_date')
    # def _compute_latest_revision_date(self):
    #     for order in self:
    #         latest_date = max(order.revision_ids.mapped('revision_date') or [False])
    #         order.revision_date = latest_date
    def _compute_latest_revision_date(self):
        for order in self:
            # collect only truthy dates (filters out False / None)
            dates = [d for d in order.revision_ids.mapped('revision_date') if d]
            # if there are valid dates use max, otherwise set to False
            order.revision_date = max(dates) if dates else False

    # Code to configure Quotation Revision button on RFQ form view
    def so_revision_quote(self):
        self.ensure_one()
        revision_count = self.env['revision.history'].search_count([('sale_id', '=', self.id)])
        # Remove previous -R# suffix if any
        base_name = self.name.split('-R')[0]

        # Save the current SO name for revision history BEFORE updating
        previous_name = self.name

        # Prepare new revision suffix
        new_revision_suffix = f"-R{revision_count + 1}"

        # Update the sale order name
        self.name = f"{base_name}{new_revision_suffix}"

        # Create new revision history record using previous_name
        revision_history = self.env['revision.history'].create({
            'sale_id': self.id,
            'name': previous_name,  # Use previous SO name here
        })

        # ######## Save all current order lines in history
        for line in self.order_line:
            self.env['revision.history.line'].create({
                'revision_history_ids': revision_history.id,
                'product_id': line.product_id.id,
                'description': line.name,
                'unit_price': line.price_unit,
                'qty': line.product_uom_qty,
            })
        ######################################
        return True


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

    is_enabled_roundoff = fields.Boolean(string="Apply Roundoff", default=True)
    amount_roundoff = fields.Monetary(string='Amount (Rounded)', compute='_compute_amount_roundoff', store=True)
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
    @api.model
    def create(self, vals):
        order = super().create(vals)
        _logger.info("vals %s", vals)
        if order.opportunity_id:
            lead = order.opportunity_id
            qualified_stage = lead.env['crm.stage'].search([('name', '=', 'Quotation')], limit=1)
            if lead.stage_id.name == 'New' and qualified_stage:
                lead.stage_id = qualified_stage.id
        try:
            auto_products = self.env['product.product'].search([
                ('product_tmpl_id.auto_add_to_sale', '=', True)
            ])

            for product in auto_products:
                self.env['sale.order.line'].create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': 1.0,
                    'price_unit': product.lst_price,
                    'product_uom': product.uom_id.id,
                    'tax_id': [(6, 0, product.taxes_id.ids)],
                })
                _logger.info("✅ Auto-added product '%s' (ID: %s) to Sale Order %s", product.name, product.id, order.name)

            if not auto_products:
                _logger.info("ℹ️ No products marked for auto-add to Sale Orders.")
        except Exception as e:
            _logger.exception("❌ Failed to auto-add products: %s", e)
        return order
    ############### remove the below code after the import is done and uncomment the above code:starts
    # @api.model
    # def create(self, vals):
    #     # Ensure the imported date_order is respected
    #     if 'date_order' in vals and vals['date_order']:
    #         vals['date_order'] = vals['date_order']  # use imported value

    #     # Call the original create method
    #     order = super(SalesTemplate, self).create(vals)

    #     # Log the vals for debugging
    #     _logger.info("vals %s", vals)

    #     # Update the related CRM opportunity stage if applicable
    #     if order.opportunity_id:
    #         lead = order.opportunity_id
    #         qualified_stage = lead.env['crm.stage'].search([('name', '=', 'Quotation')], limit=1)
    #         if lead.stage_id.name == 'New' and qualified_stage:
    #             lead.stage_id = qualified_stage.id

    #     return order
    ############### remove the below code after the import is done and uncomment the above code:ends

    def write(self, vals):
        res = super(SalesTemplate, self).write(vals)
        self._update_lead_stage()
        return res
    def _update_lead_stage(self):
        """ When a quotation is created, move linked lead to Qualified stage """
        qualified_stage = self.env['crm.stage'].search([('name', '=', 'Quotation')], limit=1)
        for order in self:
            if order.opportunity_id and qualified_stage:
                lead = order.opportunity_id
                if lead.stage_id != qualified_stage:
                    lead.stage_id = qualified_stage.id

    def action_confirm(self):
         # Check mandatory custom fields before confirming
        required_fields = [
            'partner_shipping_contact',
            'partner_shipping_mobile',
            'customer_po_no',
            'customer_po_date',
            'expected_delivery_date',
        ]

        for order in self:
            missing_fields = []
            for field_name in required_fields:
                if not order[field_name]:
                    field_label = order._fields[field_name].string
                    missing_fields.append(field_label)

            if missing_fields:
                raise UserError(
                    _("You must fill the required fields before confirming the quotation:\n%s") %
                    "\n".join(missing_fields)
                )
        res = super().action_confirm()
        for order in self:
            if order.opportunity_id:  # check quotation linked with lead
                order.opportunity_id.action_set_won()  # Mark opportunity as Won
        return res
    ############## remove the below code after the import is done and uncomment the above code:starts
    def action_confirm(self):
        # Preserve imported/assigned date_order
        for order in self:
            if order.date_order:
                preserved_date = order.date_order
            else:
                preserved_date = False

            # Call super
            res = super(SalesTemplate, order).action_confirm()

            # Restore date if it was set manually/imported
            if preserved_date:
                order.date_order = preserved_date

            # Mark linked opportunity as won
            if order.opportunity_id:
                order.opportunity_id.action_set_won()

        return res
    ############### remove the below code after the import is done and uncomment the above code:starts

    # def action_cancel(self):
    #     res = super().action_cancel()
    #     for order in self:
    #         if order.opportunity_id:
    #             # Lost reason set karvo hoy to aa rite karvo
    #             order.opportunity_id.action_set_lost(lost_reason_id=False)
    #     return res

    def action_cancel(self):
        """ Override to open cancel wizard instead of direct cancel """
        return {
            'name': 'Cancel Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def _action_cancel_with_remark(self):
        """ Actual cancel logic, called from wizard """
        res = super(SalesTemplate, self).action_cancel()
        for order in self:
            if order.opportunity_id:
                order.opportunity_id.action_set_lost(lost_reason_id=False)
        return res
    def unlink(self):
        if self.env.user.has_group('Microaccess_Purchase.group_hide_delete_button'):
            raise UserError(_("Invalid operation: You are not allowed to delete Sale Orders."))
        return super(SalesTemplate, self).unlink()
    
class SalesRemarks(models.Model):
    _name = "remarks.remarks"
    _description = "Sales Cancelled Remarks"
    _inherit=['mail.thread']
    _rec_name = "remarks"

    remarks = fields.Char(string="Sales Cancel Remarks")

class SaleOrderCancelWizard(models.TransientModel):
    _name = 'sale.order.cancel.wizard'
    _description = 'Cancel Sale Order Wizard'

    remark_id = fields.Many2one('remarks.remarks', string="Cancel Remark", required=True)

    def action_confirm_cancel(self):
        """User confirms cancellation with a remark"""
        sale_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        if sale_order:
            # Set the remark
            sale_order.cancel_remarks = self.remark_id.id
            # Call the real cancel
            sale_order._action_cancel_with_remark()

            # Explicitly set state to cancel (if _action_cancel_with_remark didn't already)
            sale_order.state = 'cancel'
        return {'type': 'ir.actions.act_window_close'}

class TermsConditions(models.Model):
    _name = 'terms.conditions'
    _description = 'Terms and Conditions' 
    _inherit=['mail.thread']
    
    name = fields.Char(string='Title', tracking=True)
    description = fields.Html(string = "Terms and Conditions")

class RevisionHistory(models.Model):
    _name = 'revision.history'
    _description = 'Revision History'
    

    name = fields.Char(string='Revision Number')
    revision_date = fields.Date(string='Revision Date', default=fields.Date.context_today)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    history_line_ids = fields.One2many('revision.history.line', 'revision_history_ids',string='Revision Sales Line')

    @api.model
    def default_get(self, fields_list):
        """ Auto-populate name from related sale order name when creating """
        res = super(RevisionHistory, self).default_get(fields_list)
        sale_id = self.env.context.get('default_sale_id')
        if sale_id:
            sale_order = self.env['sale.order'].browse(sale_id)
            if sale_order:
                res['name'] = sale_order.name
        return res

class RevisionHistoryLine(models.Model):
    _name = 'revision.history.line'
    _description = 'Revision History Line'
    _inherit=['mail.thread']

    # name = fields.Char(string='Revision History Lines')
    revision_history_ids = fields.Many2one('revision.history', string="Revision History")
    description = fields.Text(string='Description')
    unit_price = fields.Float(string='Price')
    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Float(string='Quantity')

