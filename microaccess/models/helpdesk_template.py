from odoo import fields, models, api
from datetime import datetime

class HelpdeskTemplate(models.Model):
    _inherit = "helpdesk.ticket"

    # Custom fields added to Helpdesk ticket form view
    ticket_type_service = fields.Selection([
        ('warranty', 'Warranty'),
        ('amc', 'AMC'),
        ('chargeable', 'Chargeable'),
        ('non-chargeable', 'Non-Chargeable'),
        ('fms', 'FMS'),
        ('newinstallation', 'New Installation'),
    ], string='Ticket Service Type', required=True)
    
    ticket_remarks_receiving = fields.Many2many("remarks.master", string = 'Remarks while Receiving tickets')
    ticket_nature_problem = fields.Many2many("nature.problem", string = 'Nature of Problem')
    ticket_solve_remarks = fields.Many2many("solve.remarks", string = 'Solved Remarks')
    serial_no = fields.Char(string = "Serial No.")
    qty = fields.Float(string = "Quantity")
    create_date = fields.Datetime(string = "Created Date")
    ticket_close_date = fields.Datetime(string = "Ticket Closed Date", tracking=True)
    in_progress_date = fields.Datetime(string = "New In-Progress Date", tracking=True)
    process_solved_date = fields.Datetime(string = "In-Progress Solved Date", tracking=True)
    new_in_progress = fields.Char(string = "New In-Progress Age", compute="_compute_ages")
    in_progress_solved = fields.Char(string = "Progress_Solved Age", compute="_compute_ages")
    date_age = fields.Char(string = "New-Solved Age", compute="_compute_ages")
    total_days = fields.Integer(string = "Total days", compute="_compute_total_time", readonly=True)
    total_hours = fields.Char(string = "Total Hours", readonly=True)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    current_status =fields.Selection([
        ('in-house','In-House'),
        ('vendor','Vendor'),
    ], string = 'Current Status')
    note_inward = fields.Char(string = "Note")
    response_hour = fields.Float(string = "Response Hour")
    is_repeat_ticket = fields.Boolean(string = "Is Repeat Ticket")
    ticket_rating = fields.Integer(string = 'Customer Rating')
    ticket_review = fields.Text(string ="Customer Review")
    partner_mobile = fields.Char(related='partner_id.mobile', string="Mobile", store=True, readonly=False)
    service_product_id = fields.Many2one('service.product', string="Product")
    vendor_id = fields.Many2one('res.partner', string="Vendor")
   
    assign_history_ids = fields.One2many('assign.history', 'ticket_ids', string="Assigned History")
    hold_history_ids = fields.One2many('hold.history', 'ticket_id', string="Hold History")
    
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
    @api.depends('ticket_close_date', 'in_progress_date', 'process_solved_date')
    def _compute_ages(self):
        for rec in self:
            rec.new_in_progress = rec._get_time_diff(rec.in_progress_date, rec.process_solved_date) if rec.in_progress_date and rec.process_solved_date else "0 Days, 0 Hours, 0 Minutes"
            rec.in_progress_solved = rec._get_time_diff(rec.process_solved_date, rec.ticket_close_date) if rec.process_solved_date and rec.ticket_close_date else "0 Days, 0 Hours, 0 Minutes"
            rec.date_age = rec._get_time_diff(rec.in_progress_date, rec.ticket_close_date) if rec.in_progress_date and rec.ticket_close_date else "0 Days, 0 Hours, 0 Minutes"

    # Code to compute total days and hours to populate the record under Total Days and Total hours fields
    @api.depends('ticket_close_date', 'in_progress_date')
    def _compute_total_time(self):
        for rec in self:
            if rec.ticket_close_date and rec.in_progress_date:
                time_diff = rec.ticket_close_date - rec.in_progress_date

                # Compute total days (ensure at least 1 day)
                rec.total_days = max(time_diff.days, 1)

                # Compute total hours as a string
                total_seconds = time_diff.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                rec.total_hours = f"{hours} Hours, {minutes} Minutes"
            else:
                rec.total_days = 0
                rec.total_hours = "0 Hours, 0 Minutes"
    
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
            raise exceptions.UserError("No ticket linked to this wizard.")

        previous_stage = self.ticket_id.stage_id
        self.ticket_id.stage_id = self.stage_id  # Move to the new stage
        new_stage = self.stage_id

        # Move to the new stage
        self.ticket_id.stage_id = new_stage  

        # Set date fields based on stage change
        if new_stage.name.lower() == 'in progress' and not self.ticket_id.in_progress_date:
            self.ticket_id.in_progress_date = fields.Datetime.now()
        
        if new_stage.name.lower() == 'solved':  
            if not self.ticket_id.process_solved_date:
                self.ticket_id.process_solved_date = fields.Datetime.now()
            if not self.ticket_id.ticket_close_date:  # Auto-fill ticket close date when solved
                self.ticket_id.ticket_close_date = fields.Datetime.now()

        # Auto-populate solved remarks from the wizard
            self.ticket_id.ticket_solve_remarks = [(6, 0, self.ticket_solve_remarks.ids)]
        
        # Populate the hold history fields when the stage is changed to "solved"
            self._populate_hold_history_when_solved()

        elif new_stage.name.lower() == 'hold':
            # Populate the hold history when the stage is set to "hold"
            self._populate_hold_history_when_hold()

        # Log in the chatter
        message = f"Note: {self.note}"
        self.ticket_id.message_post(body=message, subtype_xmlid="mail.mt_comment")

        return {'type': 'ir.actions.act_window_close'}
    
    def _populate_hold_history_when_hold(self):
        """Creates a hold history record when the stage is set to 'Hold'."""
        self.ticket_id.write({
            'hold_history_ids': [(0, 0, {
                'hold_date': fields.Datetime.now(),
                'hold_note': self.note,
            })]
        })

    def _populate_hold_history_when_solved(self):
        """Updates hold history record when the stage is set to 'Solved'."""
        # Check if there's an existing hold history record
        hold_history = self.ticket_id.hold_history_ids.filtered(lambda h: not h.hold_close_date)
        if hold_history:
            hold_history = hold_history[0]  # Get the first matching record

            # Update the hold history with solved date details
            hold_history.write({
                'hold_close_date': fields.Datetime.now(),
                'hold_closed_note': self.note,
                'total_time': self.ticket_id._get_time_diff(hold_history.hold_date, hold_history.hold_close_date),
                'total_days': (hold_history.hold_close_date - hold_history.hold_date).days,
            })

class AssignHistory(models.Model):
    _name = "assign.history"
    _description = "Assign History Lines"
    _inherit = ['mail.thread']

    name = fields.Char(string = "Assign history")
    ticket_ids = fields.Many2one('helpdesk.ticket', string="Helpdesk Ticket")
    assigned_to = fields.Many2one('res.users', string="Assigned To", tracking=True)
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
   