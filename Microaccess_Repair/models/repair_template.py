from odoo import fields, models, api, _

class RepairTemplate(models.Model):
    _inherit = "repair.order"

    state = fields.Selection(selection_add=[
        ('returned_without_repair', 'Return Without Repair'),
    ])

    # Custom fields added to Repair form view of Helpdesk module
    product_service_id = fields.Char(string="Product to Repair")
    warranty_expiration_date = fields.Date(string="Warranty Expiration")
    subject = fields.Char(string="Subject")
    invoice_method = fields.Selection([
        ('no_invoice', 'No Invoice'),
        ('before_repair', 'Before Repair'),
        ('after_repair', 'After Repair'),
    ], string="Invoice Method")
    remarks_ids = fields.Many2many('micro.remarks','repair_order_micro_remarks_rel', 'repair_order_id', 'mr_id', string="Remarks For Delivery")
    remarks_description = fields.Text(string="Remarks & Description")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket No.")
    partner_name = fields.Char(related="partner_id.name", string="Partner Name")
    customer_name = fields.Char(string="Customer Name")

    # Code to covert user_id field to Many2many field to allow multiple users to be assigned to a ticket starts
    user_ids = fields.Many2many('res.users', string='Responsible')

    # Optionally hide the original user_id field if not needed
    user_id = fields.Many2one('res.users', string='Responsible', compute='_compute_dummy', store=False)

    def _compute_dummy(self):
        for rec in self:
            rec.user_id = False
    # Code to covert user_id field to Many2many field to allow multiple users to be assigned to a ticket ends
   
    @api.model
    def create(self, vals):
        record = super().create(vals)
        # Code to rename repair orders to RMA/00001 from default WH/RO/00001
        if record.name:
            seq_name = self.env['ir.sequence'].next_by_code('repair.order.custom')
            record.name = seq_name

        # Link repair order to ticket form view(return_repair_id)
        if record.ticket_id:
            record.ticket_id.return_repair_id = record.id

        return record
        
    # code to display record name as RMA/00001
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name

    def write(self, vals):
        result = super().write(vals)
        for repair in self:
            if 'ticket_id' in vals and repair.ticket_id:
                repair.ticket_id.return_repair_id = repair.id
            # If sale_order_id is added or updated, update ticket
            if 'sale_order_id' in vals and repair.ticket_id:
                repair.ticket_id.sale_order_id = vals['sale_order_id']
        return result
    
    @api.model
    def default_get(self, fields_list):
        """Auto-populate product_id from related ticket's service_product_id"""
        res = super().default_get(fields_list)
        
        # Check if the repair order is being created from a ticket
        ticket_id = self._context.get('default_ticket_id')
        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            if ticket:
                res['partner_id'] = ticket.partner_id.id
                res['product_service_id'] = ticket.product_service or ''
                res['customer_name'] = ticket.customer_name or ''
        return res

    def action_return_without_repair(self):
        """Set remarks and mark as returned without repair."""
        for record in self:
            record.write({
                'state': 'returned_without_repair',
                'remarks_description': 'Return without repair',
            })
            record.message_post(body=_("Product returned to customer without repair."))
        return True
    
    def action_create_sale_order(self):
        """Override to auto-create partner if only customer_name is given."""
        for repair in self:
            # If no customer selected but customer_name is filled
            if not repair.partner_id and repair.customer_name:
                # Try to find an existing partner with that name
                existing_partner = self.env['res.partner'].search([
                    ('name', '=', repair.customer_name)
                ], limit=1)
                
                if existing_partner:
                    partner = existing_partner
                else:
                    # Create a new partner automatically
                    partner = self.env['res.partner'].create({
                        'name': repair.customer_name,
                    })
                
                # Assign the created/found partner
                repair.partner_id = partner.id

        # Now call the original logic
        return super(RepairTemplate, self).action_create_sale_order()
    
    class RepairLine(models.Model):
        _inherit = 'stock.move'

        product_id = fields.Many2one(
            'product.product', 
            string='Product', 
            required=True,
            domain=[]  # remove domain restriction completely
        )
        
class RepairTag(models.Model):
    _name = "repair.tag"
    _description = "Repair Tags"
    _inherit = ['mail.thread']
   

    name = fields.Char(string="Tag Name")
   