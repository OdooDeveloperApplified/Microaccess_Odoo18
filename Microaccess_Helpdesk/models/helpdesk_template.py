from odoo import fields, models, api, _
from datetime import datetime
import logging
import io
import xlsxwriter
import base64
from odoo.exceptions import UserError
from odoo.http import content_disposition
import math
_logger = logging.getLogger(__name__)

class HelpdeskTemplate(models.Model):
    _inherit = "helpdesk.ticket"
    # _sequence = "helpdesk.ticket.custom"
    # _rec_name = "sequence_name"


    # Custom fields added to Helpdesk ticket form view
   
    ticket_type_service = fields.Selection([
        ('warranty', 'Warranty'),
        ('amc', 'AMC'),
        ('chargeable', 'Chargeable'),
        ('non-chargeable', 'Non-Chargeable'),
        ('fms', 'FMS'),
        ('newinstallation', 'New Installation'),
    ], string='Ticket Service Type', required=True)

    # Code to covert user_id field to Many2many field to allow multiple users to be assigned to a ticket starts
    user_ids = fields.Many2many('res.users', string='Assigned To', tracking=True)

    # Optionally hide the original user_id field if not needed
    user_id = fields.Many2one('res.users', string='Assigned To', compute='_compute_dummy', store=False)
    customer_name = fields.Char(string="Customer Name")
    display_customer_name = fields.Char(
        string="Customer Name (Display)",
        compute="_compute_display_customer_name",
        store=True
    )

    @api.depends('customer_name', 'partner_id')
    def _compute_display_customer_name(self):
        """Show custom name if entered, else fallback to partner name."""
        for ticket in self:
            if ticket.customer_name:
                ticket.display_customer_name = ticket.customer_name
            else:
                ticket.display_customer_name = ticket.partner_id.name or ''

    def _compute_dummy(self):
        for rec in self:
            rec.user_id = False
    # Code to covert user_id field to Many2many field to allow multiple users to be assigned to a ticket ends
    
    ticket_remarks_receiving = fields.Many2many("remarks.master", string = 'Remarks while Receiving tickets')
    ticket_nature_problem = fields.Many2many("nature.problem", string = 'Nature of Problem')
    ticket_solve_remarks = fields.Many2many("solve.remarks", string = 'Solved Remarks')
    ticket_type_id = fields.Many2one("ticket.type", string="Ticket Type")
    serial_no = fields.Char(string = "Serial No.")
    qty = fields.Float(string = "Quantity")
    create_date = fields.Datetime(string = "Created Date")
    ticket_close_date = fields.Datetime(string = "Ticket Closed Date", tracking=True)
    in_progress_date = fields.Datetime(string = "New In-Progress Date", tracking=True)
    process_solved_date = fields.Datetime(string = "In-Progress Solved Date", tracking=True)
    new_in_progress = fields.Char(string = "New In-Progress Age", compute="_compute_ages")
    in_progress_solved = fields.Char(string = "Progress-Solved Age", compute="_compute_ages")
    date_age = fields.Char(string = "New-Solved Age", compute="_compute_ages")
    total_days = fields.Integer(string = "Total days", compute="_compute_total_time", readonly=True)
    total_hours = fields.Char(string = "Total Hours", readonly=True)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    current_status =fields.Selection([
        ('in-house','In-House'),
        ('vendor','Vendor'),
    ], string = 'Current Status')
    note_inward = fields.Char(string = "Note")
    response_hour = fields.Float(string = "Response Hour", compute = "_compute_response_hour", readonly=True)
    is_repeat_ticket = fields.Boolean(string = "Is Repeat Ticket")
    # ticket_rating = fields.Integer(string = 'Customer Rating')
    feedback = fields.Text(string ="Customer Review")
    partner_mobile = fields.Char(related='partner_id.mobile', string="Mobile", store=True, readonly=False)
    product_service = fields.Char(string="Service Product")
    service_product_id = fields.Many2one('product.product', string="Product") #service product as per MA
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    outward_challan_id = fields.Many2one('returnable.goods', string="Outward Challan No.")
    return_repair_id = fields.Many2one('repair.order', string="Return Repair Order No.")
    description = fields.Text(string="Ticket Notes")
    stage_note = fields.Text(string="Notes") # not used in form view but needed in tree view
   
    assign_history_ids = fields.One2many('assign.history', 'ticket_ids', string="Assigned History")
    hold_history_ids = fields.One2many('hold.history', 'ticket_id', string="Hold History")
    product_line_ids = fields.One2many('line.product', 'ticket_id', string="Multiple Products")
    
    # Code to get the format required to calculate date related fields
    def _get_time_diff(self, start, end):
        """ Returns time difference in a formatted string: 'X Days, Y Hours, Z Minutes' """
        if start and end:
            diff = end - start
            days = diff.days
            hours = diff.seconds // 3600
            minutes = (diff.seconds % 3600) // 60
            return f"{days} Days, {hours} Hours, {minutes} Minutes"
        return "0 Days, 0 Hours, 0 Minutes"


    # Code to calculate the date related fields when the ticket moves through different stages
    @api.depends('ticket_close_date', 'in_progress_date', 'process_solved_date','create_date')
    def _compute_ages(self):
        for rec in self:
            # old code (considering the actual data flow calculation starts when the ticket is in progress state)
            # rec.new_in_progress = rec._get_time_diff(rec.in_progress_date, rec.process_solved_date) if rec.in_progress_date and rec.process_solved_date else "0 Days, 0 Hours, 0 Minutes"
            # rec.in_progress_solved = rec._get_time_diff(rec.process_solved_date, rec.ticket_close_date) if rec.process_solved_date and rec.ticket_close_date else "0 Days, 0 Hours, 0 Minutes"
            # rec.date_age = rec._get_time_diff(rec.in_progress_date, rec.ticket_close_date) if rec.in_progress_date and rec.ticket_close_date else "0 Days, 0 Hours, 0 Minutes"
            
            # New code (considering the actual data flow calculation starts when the ticket is created)
            rec.new_in_progress = rec._get_time_diff(rec.create_date, rec.in_progress_date) if rec.create_date and rec.in_progress_date else "0 Days, 0 Hours, 0 Minutes"
            rec.in_progress_solved = rec._get_time_diff(rec.in_progress_date, rec.process_solved_date) if rec.in_progress_date and rec.process_solved_date else "0 Days, 0 Hours, 0 Minutes"
            rec.date_age = rec._get_time_diff(rec.create_date, rec.ticket_close_date) if rec.create_date and rec.ticket_close_date else "0 Days, 0 Hours, 0 Minutes"
    
    # Code to compute total days and hours to populate the record under Total Days and Total hours fields (calculation in accordance to old code)
    # OLD CODE CONSIDERING 24 HOURS WORKING TIME
    # @api.depends('ticket_close_date', 'create_date')
    # def _compute_total_time(self):
    #     for rec in self:
    #         if rec.ticket_close_date and rec.create_date:
    #             time_diff = rec.ticket_close_date - rec.create_date

    #             # Compute total days (ensure at least 1 day)
    #             total_seconds = time_diff.total_seconds()
    #             rec.total_days = math.ceil(total_seconds / (24 * 3600)) # 86400 seconds in a day

    #             # Compute total hours as a string
    #             hours = int(total_seconds // 3600)
    #             minutes = int((total_seconds % 3600) // 60)
    #             rec.total_hours = f"{hours} Hours, {minutes} Minutes"
    #         else:
    #             rec.total_days = 0
    #             rec.total_hours = "0 Hours, 0 Minutes"

    # NEW CODE CONSIDERING 8 HOURS WORKING TIME
    @api.depends('ticket_close_date', 'create_date')
    def _compute_total_time(self):
        for rec in self:
            if rec.ticket_close_date and rec.create_date:
                time_diff = rec.ticket_close_date - rec.create_date

                # Compute total days (unchanged — calendar days)
                total_seconds = time_diff.total_seconds()
                rec.total_days = math.ceil(total_seconds / (24 * 3600))  # 86400 seconds in a day

                # ------------------ UPDATED: working-hours via 8h-day mapping ------------------
                total_hours_float = total_seconds / 3600.0                         # total calendar hours
                full_calendar_days = int(total_hours_float // 24)                 # number of full 24h days
                # deduct 16 hours per full calendar day to map 24h -> 8h
                working_hours_total = total_hours_float - (16.0 * full_calendar_days)

                # produce Hours, Minutes string from working_hours_total
                wh_hours = int(working_hours_total)                               # full working hours
                wh_minutes = int((working_hours_total * 60) % 60)                 # leftover minutes
                rec.total_hours = f"{wh_hours} Hours, {wh_minutes} Minutes"
                # ---------------------------------------------------------------------------
            else:
                rec.total_days = 0
                rec.total_hours = "0 Hours, 0 Minutes"

   
    
    # Code to compute response hour based on the difference between create_date and in_progress_date
    # OLD CODE CONSIDERING 24 HOURS WORKING TIME
    # @api.depends('create_date', 'in_progress_date')
    # def _compute_response_hour(self):
    #     for rec in self:
    #         if rec.create_date and rec.in_progress_date:
    #             time_diff = rec.in_progress_date - rec.create_date
    #             total_hours = time_diff.total_seconds() / 3600
    #             rec.response_hour = round(total_hours, 2)
    #         else:
    #             rec.response_hour = 0.0

    # NEW CODE CONSIDERING 8 HOURS WORKING TIME
    @api.depends('create_date', 'in_progress_date')
    def _compute_response_hour(self):
        for rec in self:
            if rec.create_date and rec.in_progress_date:
                time_diff = rec.in_progress_date - rec.create_date
                total_hours = time_diff.total_seconds() / 3600.0

                # Deduct 16 hours per full calendar day so 24h -> 8h mapping
                full_calendar_days = int(total_hours // 24)
                working_hours = total_hours - (16.0 * full_calendar_days)

                rec.response_hour = round(working_hours, 2)
            else:
                rec.response_hour = 0.0

    # Code to define action to open wizard on clicking "Change Stages" button
    def open_change_stages_wizard(self):
        """Opens the wizard for changing the stage."""
        return {
            'name': 'Change Stages',
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ticket_id': self.id},
        }
    
    # Code to define action related to creating returnable goods record in Helpdesk ticket form view when clicking on In-out Challan button
    def open_in_out_challan(self):
        self.ensure_one()
        returnable = self.env['returnable.goods'].create({
            'ticket_id': self.id,
            # 'partner_id': self.partner_id.id,
            'customer_id': self.partner_id.id,
            'challan_date': fields.Date.today(),
        })
        self.outward_challan_id = returnable.id

        # Log message in chatter
        # vendor_name = self.vendor_id.name or "N/A"
        challan_number = returnable.challan_no or "Draft"
        self.message_post(
            body=f"Outward Number → {challan_number}",
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

        # self.message_post(
        #     body=f"Vendor → {vendor_name}",
        #     message_type="comment",
        #     subtype_xmlid="mail.mt_note",
        # )
        return {
            'name': 'Returnable Goods',
            'type': 'ir.actions.act_window',
            'res_model': 'returnable.goods',
            'view_mode': 'form',
            'res_id': returnable.id,
            'target': 'current',
        }
    
    # Code to populate the Assign History records
    @api.model
    def create(self, vals):
        _logger.info("this is custom create helpdesk %s", vals)
        record = super().create(vals)
        if vals.get('user_ids'):
            record._create_assign_history(vals['user_ids'])

        # Code to rename ticket name record
        if record.name:
            seq_name = self.env['ir.sequence'].next_by_code('helpdesk.ticket.custom')
            record.name = record.name + "(" + seq_name +")"
            record.ticket_ref = seq_name
        return record

    # Code to display desired name format {Subject(create_date/sequence)}
    def _compute_display_name(self):
        for ticket in self:
            ticket.display_name = ticket.name
    
    @api.model
    def _send_custom_rating_mail(self, ticket):
        """Send custom rating email."""
        template = self.env.ref(
            'Microaccess_Helpdesk.custom_rating_ticket_request_email_template',
            raise_if_not_found=False
        )
        if not template:
            return

        template.sudo().send_mail(ticket.id, force_send=True)
            
    # Code to populate data for assign history records
    def write(self, vals):
        # assigned_changed = 'user_ids' in vals
        # if assigned_changed:
        #     old_users = self.user_ids.mapped('name')


        # Store stage before write (required for email trigger logic) starts
        stage_before = {t.id: t.stage_id.id for t in self} ############################ ends

        for ticket in self:
            # Handle Many2many commands safely
            new_user_cmd = vals.get('user_ids')
            if new_user_cmd:
                new_user_ids = []
                if isinstance(new_user_cmd[0], (list, tuple)):
                    for cmd in new_user_cmd:
                        if cmd[0] == 6:
                            new_user_ids = cmd[2]
                        elif cmd[0] == 4:
                            new_user_ids.append(cmd[1])
                        elif cmd[0] == 3:
                            old_ids = ticket.user_ids.ids
                            # SAFE REMOVE
                            if cmd[1] in old_ids:
                                old_ids.remove(cmd[1])
                            new_user_ids = old_ids
                else:
                    new_user_ids = new_user_cmd

                old_user_ids = ticket.user_ids.ids

                # Only update assign history if there’s a change
                if set(new_user_ids) != set(old_user_ids):
                    ticket._close_previous_assign_history()
                    ticket._create_assign_history(new_user_ids)

            if 'stage_id' in vals:
                new_stage = self.env['helpdesk.stage'].browse(vals['stage_id'])
                if new_stage and new_stage.name.lower() == 'solved':
                    ticket._close_previous_assign_history()

        result = super().write(vals)

        # if assigned_changed:
        #     new_users = self.user_ids.mapped('name')

        #     message = (
        #         f"Assigned To Updated by: {self.env.user.name},"
        #         f"Old Assigned Users: {', '.join(old_users) or 'None'},"
        #         f"New Assigned Users: {', '.join(new_users) or 'None'}"
        #     )

        #     self.message_post(body=message)

        # ---------------------------
        # AFTER SUPER: your rating-email logic (added safely) start
        # ---------------------------
        for ticket in self:
            if 'stage_id' in vals:
                old_stage = stage_before.get(ticket.id)
                new_stage = ticket.stage_id.id

                solved_stage = self.env.ref(
                    'helpdesk.stage_solved',  # update if custom
                    raise_if_not_found=False
                )

                if solved_stage and new_stage == solved_stage.id and old_stage != new_stage:

                    # STOP SYSTEM EMAIL: unfollow customer starts
                    partner = ticket.partner_id
                    if partner and partner in ticket.message_partner_ids:
                        ticket.message_unsubscribe(partner_ids=[partner.id])
                    # STOP SYSTEM EMAIL: unfollow customer ends

                    ticket._send_custom_rating_mail(ticket)
        ######### ends ####################

        return result

    def _create_assign_history(self, user_ids):
        self.assign_history_ids = [(0, 0, {
            'assigned_to': user_ids,
            'assign_date': fields.Datetime.now(),
        })]

    def _close_previous_assign_history(self):
        last_assign = self.assign_history_ids.filtered(lambda h: not h.assign_close_date)
        if last_assign:
            last_assign.assign_close_date = fields.Datetime.now()
    
    # Code to define action to open returnable goods form view
    # on clicking "Returnable Goods" button
    returnable_goods_ids = fields.One2many('returnable.goods', 'ticket_id', string="Returnable Goods")

    def action_view_returnable_goods(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Returnable Goods',
            'res_model': 'returnable.goods',
            'view_mode': 'list,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }
    ######################## Custom Email Template related code starts ##################################################
    
    rating_avg_text = fields.Selection(
        selection_add=[('excellent', 'Excellent')],
        # keep same string and other params as before if needed
    )
    # rating_last_value = fields.Float(string='Last Rating Value', compute='_compute_last_rating_value')

    # def _compute_last_rating_value(self):
    #     for ticket in self:
    #         last_rating = self.env['rating.rating'].search([
    #             ('res_model', '=', 'helpdesk.ticket'),
    #             ('res_id', '=', ticket.id),
    #             ('consumed', '=', True),
    #         ], order='write_date desc', limit=1)
    #         ticket.rating_last_value = last_rating.rating or 0
       
    rating_last_value = fields.Integer(
        string="Customer Rating",
        compute="_compute_rating_last_value",
        store=True
    )

    def _compute_rating_last_value(self):
        for ticket in self:
            rating = ticket.rating_ids.sorted('create_date', reverse=True)[:1]
            ticket.rating_last_value = rating.rating if rating else 0

    ######################## Custom Email Template related code ends ##################################################

    ################################ Multi ticket login user access code starts #############################################

    @api.model
    def get_user_tickets(self):
        """Return helpdesk tickets visible to the current user"""
        if not self.env.user.has_group('base.group_system'):
            # For regular users: Only their assigned tickets
            # tickets = self.env['helpdesk.ticket'].search([('user_ids', 'in', [self.env.uid])])
            tickets = self.env['helpdesk.ticket'].search([
                '|',
                ('user_ids', '=', False),
                ('user_ids', 'in', [self.env.uid])
            ])
        else:
            # For admin/system user: All tickets
            tickets = self.env['helpdesk.ticket'].search([])
        # You can return, log, or process tickets as needed
        return tickets
    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        if self.user_ids:
            self.user_id = self.user_ids[0]
        else:
            self.user_id = False
    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        if not self.env.user.has_group('base.group_system'):
            # args = args + [('user_ids', 'in', [self.env.uid])]
            args = args + [
                '|',
                ('user_ids', '=', False),
                ('user_ids', 'in', [self.env.uid])
            ]
        return super(HelpdeskTemplate, self).search(args, offset=offset, limit=limit, order=order)
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if not self.env.user.has_group('base.group_system'):
            # domain += [('user_ids', 'in', [self.env.uid])]
            domain = domain + [
                '|',
                ('user_ids', '=', False),
                ('user_ids', 'in', [self.env.uid])
            ]
        return super(HelpdeskTemplate, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if not self.env.user.has_group('base.group_system'):
            # domain = (domain or []) + [('user_ids', 'in', [self.env.uid])]
             domain = (domain or []) + [
                '|',
                ('user_ids', '=', False),
                ('user_ids', 'in', [self.env.uid])
            ]
        return super(HelpdeskTemplate, self).search_read(domain, fields=fields, offset=offset, limit=limit, order=order)
    # @api.model
    # def read(self, fields=None, load='_classic_read'):
    #     if not self.env.user.has_group('base.group_system'):
    #         for rec in self:
    #             if self.env.uid not in rec.user_ids.ids:
    #                 raise AccessError("You are not allowed to read this ticket.")
    #     return super(HelpdeskTicket, self).read(fields=fields, load=load)
    @api.model
    def read(self, fields=None, load='_classic_read'):
        if not self.env.user.has_group('base.group_system'):
            # Filter out records user is NOT assigned to before reading
            # allowed_records = self.filtered(lambda rec: self.env.uid in rec.user_ids.ids)
            allowed_records = self.filtered(
                lambda rec: not rec.user_ids or self.env.uid in rec.user_ids.ids
            )
            if not allowed_records:
                # Return empty list if no accessible records
                
                # return super(HelpdeskTemplate, self).read(fields=fields, load=load)
                return []
            return super(HelpdeskTemplate, allowed_records).read(fields=fields, load=load)
        return super(HelpdeskTemplate, self).read(fields=fields, load=load)
    ################################ Multi ticket login user access code ends #############################################
class RemarksMaster(models.Model):
    _name = "remarks.master"
    _description = "Remarks Receiving Master"
    _inherit=['mail.thread']
    _rec_name = "receiving_name"

    receiving_name = fields.Char(string="Ticket Receiving Master")

class NatureProblem(models.Model):
    _name = "nature.problem"
    _description = "Nature of Problem"
    _inherit=['mail.thread']
    _rec_name = "nature_problem"

    nature_problem = fields.Char(string="Ticket Nature of Problem")

class SolveRemarks(models.Model):
    _name = "solve.remarks"
    _description = "Solved Remarks"
    _inherit=['mail.thread']
    _rec_name = "solve_remarks"

    solve_remarks = fields.Char(string="Ticket Solve Remarks")

class ServiceProductMaster(models.Model):
    _name = "service.product"
    _description = "Service Product Master"
    _inherit=['mail.thread']
    
    name = fields.Char(string="Product Name")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    description = fields.Text(string='Description')

class TicketTypeMaster(models.Model):
    _name = "ticket.type"
    _description = "Helpdesk Ticket Type Master"
    _order = 'sequence, name'
    
    
    name = fields.Char(string="Ticket Type")
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "A type with the same name already exists."),
    ]
    
class HelpdeskTicketWizard(models.Model):
    _name = 'helpdesk.ticket.wizard'
    _description = 'Change Stages Wizard'
    _inherit = ['mail.thread']

    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket", required=True)
    stage_id = fields.Many2one('helpdesk.stage', string="Stage", required=True, tracking=True)
    note = fields.Text(string="Note", required=True, tracking=True)
    ticket_solve_remarks = fields.Many2many("solve.remarks", string = 'Solved Remarks')

    def action_change_stage(self):
        """Updates the ticket stage and logs the change in chatter."""
        if not self.ticket_id:
            raise UserError("No ticket linked to this wizard.")

        new_stage = self.stage_id

        # Set the stage
        self.ticket_id.stage_id = new_stage
        self.ticket_id.stage_note = self.note # not used in form view but needed in tree view to show the note related to respective stage 

        # Set date fields and history tracking
        stage_name = new_stage.name.lower()

        if stage_name == 'in progress':
            if not self.ticket_id.in_progress_date:
                self.ticket_id.in_progress_date = fields.Datetime.now()

            # Close hold history if any open
            self._populate_hold_history_when_solved()

        elif stage_name == 'solved':
            _logger.info("Moving ticket to Solved stage %s", self.ticket_id)
            if not self.ticket_id.process_solved_date:
                self.ticket_id.process_solved_date = fields.Datetime.now()
            if not self.ticket_id.ticket_close_date:
                self.ticket_id.ticket_close_date = fields.Datetime.now()

            # Add solved remarks
            self.ticket_id.ticket_solve_remarks = [(6, 0, self.ticket_solve_remarks.ids)]

        elif stage_name == 'on hold':
            _logger.info("Moving ticket to Hold stage %s", self.ticket_id)
            self._create_hold_history_record()

        # Post note in chatter
        self.ticket_id.message_post(body=f"Note: {self.note}", subtype_xmlid="mail.mt_comment")

        return {'type': 'ir.actions.act_window_close'}

    # Code to populate hold history records when the ticket is moved to Hold stage
    def _create_hold_history_record(self):
        """Create a new hold history line when moved to Hold stage."""
        _logger.info("Creating hold history record %s", self.ticket_id)  
        self.ticket_id.write({
            'hold_history_ids': [(0, 0, {
                'hold_date': fields.Datetime.now(),
                'hold_note': self.note,
            })]
        })
        # self.env['hold.history'].sudo().create({'ticket_id': self.ticket_id.id,
        #                                         'hold_date': fields.Datetime.now(),
        #                                         'hold_note': self.note,
        #                                         })

    def _populate_hold_history_when_solved(self):
        """Close the last open hold history record when solved."""
        open_hold = self.ticket_id.hold_history_ids.filtered(lambda h: not h.hold_close_date)
        if open_hold:
            hold = open_hold[0]
            now = fields.Datetime.now()
            hold.write({
                'hold_close_date': now,
                'hold_closed_note': self.note,
                'total_time': self.ticket_id._get_time_diff(hold.hold_date, now),
                'total_days': (now - hold.hold_date).days,
            })

class AssignHistory(models.Model):
    _name = "assign.history"
    _description = "Assign History Lines"
    _inherit = ['mail.thread']

    name = fields.Char(string = "Assign history")
    ticket_ids = fields.Many2one('helpdesk.ticket', string="Helpdesk Ticket")
    assigned_to = fields.Many2many('res.users', string="Assigned To", tracking=True)
    assign_date = fields.Datetime(string="Assign Date", default=fields.Datetime.now, tracking=True)
    assign_close_date = fields.Datetime(string="Assign Close Date", tracking=True)

class HoldHistory(models.Model):
    _name = "hold.history"
    _description = "Hold History Lines"
    _inherit = ['mail.thread']

    name = fields.Char(string="Hold history")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Helpdesk ticket")
    hold_date = fields.Datetime(string="Hold Date")
    hold_close_date = fields.Datetime(string="Hold Closed Date")
    total_time = fields.Char(string="Total Time")
    total_days = fields.Integer(string="Total Days")
    hold_note = fields.Char(string="Hold Note")
    hold_closed_note = fields.Char(string="Hold Closed Note")

class LineProduct(models.Model):
    _name = "line.product"
    _description ="Multiple Product Lines"

    service_product_id = fields.Many2one('product.product', string="Product")
    serial_numer = fields.Char(string="Serial No.")
    quantity = fields.Float(string="Quantity")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Helpdesk ticket")

class ReturnableGoods(models.Model):
    _name = "returnable.goods"
    _description = "Returnable Goods"
    _inherit=['mail.thread']
    _sequence = 'returnable.goods'  # Sequence code to use for numbering
    _rec_name = 'challan_no' 

    challan_no = fields.Char(string="Challan No.", required=True, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string="Vendor")
    ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket No.")
    repair_order_id = fields.Many2one('repair.order', string="Repair Order No.")
    return_date = fields.Date(string="Return Date")
    customer_id = fields.Many2one('res.partner', string="Customer")
    customer_name = fields.Char(related="customer_id.name", string="Customer Name")
    challan_date = fields.Date(string="Challan Date")
    remarks = fields.Many2many('micro.remarks', string="Remarks")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('repair', 'Repair'),
        ('return', 'Return'),
        ('cancel', 'Cancel')
    ], string="Status", default='draft', tracking=True)
    over_estimate = fields.Char(string="Over Estimate")
    revised_estimate = fields.Char(string="Revised Estimate")
    customer_estimate = fields.Char(string="Customer Estimate")

    # computed boolean to control readonly
    over_estimate_readonly = fields.Boolean(
        compute='_compute_over_estimate_readonly',
        store=True
    )
    followup_line_ids = fields.One2many('returnable.goods.followup','returnable_id',string="Follow Ups")

    @api.depends('over_estimate')
    def _compute_over_estimate_readonly(self):
        for record in self:
            # readonly if over_estimate is set and record exists
            record.over_estimate_readonly = bool(record.over_estimate) and bool(record.id)

    def write(self, vals):
        for record in self:
            if record.over_estimate and 'over_estimate' in vals:
                raise UserError("You cannot modify Over Estimate once it is set.")
        res = super().write(vals)

        if 'partner_id' in vals:
            for rec in self:
                if rec.ticket_id and rec.partner_id:
                    rec.ticket_id.vendor_id = rec.partner_id
                # Log vendor info in ticket chatter
                rec.ticket_id.message_post(
                    body=f"Vendor → {rec.partner_id.name}",
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )

        if 'state' in vals and vals.get('state') in ('return', 'repair'):
            for rec in self:
                if rec.ticket_id:
                    rec.ticket_id.write({
                        'current_status': 'in-house'
                    })

        return res

    # Code to link returnable goods lines and return received quantities to the returnable goods
    returnable_goods_line_ids = fields.One2many('returnable.goods.line', 'returnable_goods_id', string="Returnable Goods Lines")
    return_received_qty_ids = fields.One2many('return.received.qty.line', 'returnable_goods_id', string="Return Received Quantities")
    
    # Code to create Challan number sequence
    @api.model
    def create(self, vals):
    # Auto-fill challan number using sequence
        if vals.get('challan_no', _('New')) == _('New'):
            vals['challan_no'] = self.env['ir.sequence'].next_by_code('returnable.goods') or _('New')

        # Auto-link the related repair order if ticket is provided
        if vals.get('ticket_id') and not vals.get('repair_order_id'):
            ticket = self.env['helpdesk.ticket'].browse(vals['ticket_id'])
            if ticket.return_repair_id:
                vals['repair_order_id'] = ticket.return_repair_id.id

        record = super().create(vals)

        # --- New code to update ticket vendor ---
        if record.ticket_id and record.partner_id:
            record.ticket_id.vendor_id = record.partner_id

        return record

    # def write(self, vals):
    #     res = super().write(vals)
    #     # --- Update ticket vendor if partner_id is changed ---
    #     if 'partner_id' in vals:
    #         for rec in self:
    #             if rec.ticket_id and rec.partner_id:
    #                 rec.ticket_id.vendor_id = rec.partner_id
    #             # Log vendor info in ticket chatter
    #             rec.ticket_id.message_post(
    #                 body=f"Vendor → {rec.partner_id.name}",
    #                 message_type="comment",
    #                 subtype_xmlid="mail.mt_note",
    #             )
    #     return res

    # Code to define action on buttons provided in header section of the form view
    def action_start_progress(self):
        self.state = 'in_progress'

    def action_repair(self):
        self.ensure_one()
        return {
            'name': 'Return Received Quantity Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'return.received.qty.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_returnable_goods_id': self.id,
            }
        }
    
    def action_return_without_repair(self):
        self.ensure_one()
        return {
            'name': 'Close Challan',
            'type': 'ir.actions.act_window',
            'res_model': 'returnable.challan.close.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_challan_id': self.id,
            }
        }

    def action_cancel(self):
        self.state = 'cancel'

class ReturnableGoodsFollowup(models.Model):
    _name = "returnable.goods.followup"
    _description = "Returnable Goods Followup"

    returnable_id = fields.Many2one("returnable.goods", string="Returnable Goods")
    followup_date = fields.Date(string="Date")
    followup_text = fields.Text(string="Comments")


class ReturnableGoodsLine(models.Model):
    _name = 'returnable.goods.line'
    _description = 'Returnable Goods Line'

    returnable_goods_id = fields.Many2one('returnable.goods', string="Returnable Goods")
    product_id = fields.Many2one('product.product', string="Product") 
    product_name = fields.Char(string="Product Name")
    description = fields.Text(string="Description")
    serial_no = fields.Char(string="Serial/Lot No.")
    hsn_code_id = fields.Many2one('product.template', string="HSN/SAC Code")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    qty_available = fields.Float(string="Quantity Available")
    dummy_qty_available = fields.Float(string="Dummy Quantity Available")
    qty = fields.Float(string="Quantity")
    is_received = fields.Boolean(string="Received")
    return_qty = fields.Float(string="Return Quantity")
    rate = fields.Float(string="Rate")
    amount = fields.Float(string="Amount")
    today_return_date = fields.Date(string="Date")
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note')
    ], string="Display Type", default=None)
    

class ReturnReceivedQtyLine(models.Model):
    _name = 'return.received.qty.line'
    _description = 'Return Received Quantity Line'

    returnable_goods_id = fields.Many2one('returnable.goods', string="Returnable Goods")
    product_id = fields.Many2one('product.product', string="Product") #service product as per MA
    product_name = fields.Char(string="Product Name")
    serial_no = fields.Char(string="Serial/Lot No.")
    hsn_code_id = fields.Char(string="HSN/SAC Code")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    qty = fields.Float(string="Quantity")
    rate = fields.Float(string="Rate")
    amount = fields.Float(string="Amount")
    subsidiary_challan_no = fields.Char(string="Subsidiary Challan No.")
    return_date = fields.Date(string="Return Date")


class ReturnQuantityLine(models.TransientModel):
    _name = 'return.quantity.line'
    _description = 'Return Quantity Line'
    
    return_qty_id = fields.Many2one('return.received.qty.wizard', string="Return Wizard")
    returnable_goods_line_id = fields.Many2one('returnable.goods.line', string="Returnable Goods Line")
    product_id = fields.Many2one('product.product', string="Product")
    product_name = fields.Char(string="Product Name")
    description = fields.Text(string="Description")
    serial_no = fields.Char(string="Serial/Lot No.")
    hsn_code_id = fields.Char(string="HSN/SAC Code")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    qty = fields.Float(string="Quantity")
    rate = fields.Float(string="Rate")
    amount = fields.Float(string="Amount")
    subsidiary_challan_no = fields.Char(string="Subsidiary Challan No.")
    return_qty = fields.Float(string="Return Quantity")
    return_date = fields.Date(string="Return Date")

    original_qty = fields.Float(string="Original Quantity", readonly=True)

    @api.onchange('return_qty')
    def _onchange_return_qty(self):
        if not self.original_qty:
            self.original_qty = self.qty + self.return_qty  # Fallback for safety

        if self.return_qty > self.original_qty:
            self.return_qty = self.original_qty  # Limit return_qty

        self.qty = self.original_qty - self.return_qty

class ReturnReceivedWizard(models.TransientModel):
    _name = 'return.received.qty.wizard'
    _description = 'Return Received Quantity Wizard'

    returnable_goods_id = fields.Many2one('returnable.goods', string="Returnable Goods")
    subsidiary_challan_no = fields.Char(string="Subsidiary Challan No.")
    return_date = fields.Date(string="Return Date")
    return_quantity_line_ids = fields.One2many('return.quantity.line', 'return_qty_id', string="Return Quantity Lines")
    returnable_goods_line_id = fields.Many2one('returnable.goods.line', string="Returnable Goods Line", invisible=True)

    @api.model
  
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        returnable_goods_id = self.env.context.get('default_returnable_goods_id')
        if returnable_goods_id:
            res['returnable_goods_id'] = returnable_goods_id
            
            returnable_lines = self.env['returnable.goods.line'].search([
                ('returnable_goods_id', '=', returnable_goods_id),
                ('qty', '>', 0),  # Get lines where qty > 0 (reflects latest available)
                ('display_type', '=', False),
            ])
            
            return_lines = []
            for line in returnable_lines:
                original_quantity = line.qty or 0.0 
                remaining_quantity = original_quantity - (line.return_qty or 0.0)
                return_lines.append((0, 0, {
                    'returnable_goods_line_id': line.id,
                    'product_id': line.product_id.id if line.product_id else False,
                    'product_name': line.product_name or (line.product_id.name if line.product_id else ''),
                    'description': line.description or '',
                    'serial_no': line.serial_no or '',
                    'hsn_code_id': line.hsn_code_id.name if line.hsn_code_id else '',
                    'uom_id': line.uom_id.id if line.uom_id else False,
                    'qty': remaining_quantity,            # The CURRENT qty from returnable.goods.line
                    'original_qty': remaining_quantity,   # Set original qty same as current
                    'rate': line.rate or 0.0,
                    'amount': line.amount or 0.0,
                    'return_qty': 0.0,         # Start with 0 return by default
                    'return_date': line.today_return_date ,
                }))
            
            res['return_quantity_line_ids'] = return_lines
        
        return res

    def action_confirm(self):
        self.ensure_one()
        
        if not self.return_quantity_line_ids:
            raise UserError("No products found to return.")
        
        lines_with_qty = self.return_quantity_line_ids.filtered(lambda x: x.return_qty > 0)
        if not lines_with_qty:
            raise UserError("Please enter return quantity for at least one product.")
        
        for return_line in lines_with_qty:
            # if return_line.return_qty > return_line.original_qty:
            #     raise UserError(f"Return quantity ({return_line.return_qty}) cannot exceed original quantity ({return_line.original_qty}) for product {return_line.product_name}")
            
            vals = {
                'returnable_goods_id': self.returnable_goods_id.id,
                'product_id': return_line.product_id.id if return_line.product_id else False,
                'product_name': return_line.product_name or '',
                'serial_no': return_line.serial_no or '',
                'hsn_code_id': return_line.hsn_code_id or '',
                'uom_id': return_line.uom_id.id if return_line.uom_id else False,
                'qty': return_line.return_qty,
                'rate': return_line.rate or 0.0,
                'amount': return_line.amount or 0.0,
                'subsidiary_challan_no': return_line.subsidiary_challan_no or self.subsidiary_challan_no or '',
                'return_date': return_line.return_date or self.return_date,
            }
            self.env['return.received.qty.line'].create(vals)

            # Update the corresponding returnable goods line quantities
            _logger.info("Updating returnable goods line %s", return_line.read())
            
            if return_line.returnable_goods_line_id:
                line = return_line.returnable_goods_line_id
                returned_qty = return_line.return_qty or 0.0
                if returned_qty > 0:
                    line.sudo().write({
                        'return_qty': (line.return_qty or 0.0) + returned_qty,
                        # 'qty': max((line.qty or 0.0) - returned_qty, 0.0)
                    })
             # Only change state if all quantities are zero after return
            all_returnd = all(
                line.returnable_goods_line_id and
                (line.returnable_goods_line_id.return_qty == line.returnable_goods_line_id.qty)
                for line in self.return_quantity_line_ids
            )
            if all_returnd:
                self.returnable_goods_id.state = 'repair'

        
        return {'type': 'ir.actions.act_window_close'}
       
class ReturnableChallanCloseWizard(models.TransientModel):
    _name = 'returnable.challan.close.wizard'
    _description = 'Returnable Challan Close Wizard'

    challan_id = fields.Many2one('returnable.goods', string="Challan No.", required=True)
    reason = fields.Text(string="Reason", required=True)
    return_date = fields.Date(string="Return Date", required=True)

    # Code to define action linked to Close challan wizard
    def action_close_challan(self): 
        """Close the returnable goods challan."""
        if not self.challan_id:
            raise UserError("No challan linked to this wizard.")

        challan = self.challan_id
        challan.write({
            'return_date': self.return_date,
            'state': 'return',
            
        })
        return {'type': 'ir.actions.act_window_close'}

class HelpdeskReportWizard(models.TransientModel):
    _name = 'helpdesk.report.wizard'
    _description = 'In-Progress Helpdesk Ticket XLS Report'

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    file_download = fields.Binary("Download Excel", readonly=True)
    file_name = fields.Char("File Name")
    file_data = fields.Binary('Report File')

    def action_generate_report(self):
        # Filter only tickets in 'In Progress' stage within the given date range  
        tickets = self.env['helpdesk.ticket'].search([
            ('create_date', '>=', self.from_date),
            ('create_date', '<=', self.to_date),
            
        ])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("InProgress Report")

        # Define formatting
        bold = workbook.add_format({'align': 'center', 'valign': 'vcenter','border': 1, 'bold': True, 'text_wrap': True, 'bg_color': '#DEEBF7'})
        title_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'font_size': 18, 'border': 1
        })
        subtitle_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'left', 'valign': 'vcenter'
        })
        text_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter','border': 1, 'text_wrap': True
        })

        # Set row height for better appearance
        worksheet.set_row(0, 30)  # Title row (A1:I1)
        worksheet.set_row(1, 25)  # Subtitle row (A2:I2)
        worksheet.set_row(3, 25)

        # Merge cells for the report title
        worksheet.merge_range('A1:I1', 'In Progress Excel Report', title_format)

        # Merge cells for the subtitle (From and To date in same row)
        subtitle_text = f"From Date: {self.from_date.strftime('%d-%m-%Y')}   To Date: {self.to_date.strftime('%d-%m-%Y')}"
        worksheet.merge_range('A2:I2', subtitle_text, subtitle_format)

        # Column headers
        headers = [
            'Sr. No.', 'Subject', 'Customer', 'Customer Name',
            'Create Date', 'In Progress Date', 'New-In Progress Age',
            'Response Time', 'Sale Order'
        ]
        worksheet.write_row(3, 0, headers, bold)  # Start headers at row index 3 (Excel row 4)

        # Populate ticket data
        row = 4  # Data starts from row index 4 (Excel row 5)
        for idx, ticket in enumerate(tickets, start=1):
            worksheet.write(row, 0, idx, text_format)  # Sr No.
            worksheet.write(row, 1, ticket.name or '', text_format)  # Subject
            worksheet.write(row, 2, ticket.partner_id.name or '', text_format)  # Customer
            worksheet.write(row, 3, ticket.partner_id.display_name or '', text_format)  # Customer Name
            worksheet.write(row, 4, ticket.create_date.strftime('%d-%m-%Y') or '', text_format)  # Create Date
            in_progress_date = ticket.in_progress_date.strftime('%d-%m-%Y') if ticket.in_progress_date else ''
            worksheet.write(row, 5, in_progress_date, text_format) # In Progress Date
            worksheet.write(row, 6, ticket.new_in_progress or '', text_format)  # New-In Progress Age

            # Response Time = difference between create_date and in_progress_date in HH:MM
            response = ''
            if ticket.create_date and ticket.in_progress_date:
                delta = ticket.in_progress_date - ticket.create_date
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                response = f"{hours:02}:{minutes:02}"
            worksheet.write(row, 7, response, text_format)

            worksheet.write(row, 8, ticket.sale_order_id.name or '', text_format)  # Sale order
            row += 1

        # Auto-adjust column widths
        column_widths = [10, 30, 25, 30, 20, 20, 25, 15, 20]
        for col_num, width in enumerate(column_widths):
            worksheet.set_column(col_num, col_num, width)

        # Finish workbook
        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())
        file_name = f"In Progress Excel Report({datetime.now().strftime('%d/%m/%Y')}).xlsx"
        self.write({'file_data': file_data, 'file_name': file_name})
        output.close()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=helpdesk.report.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }
    



   