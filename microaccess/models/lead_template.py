from odoo import fields, models, api
import io
import xlsxwriter
import base64
from odoo.tools.safe_eval import safe_eval
from datetime import datetime, date
# from datetime import date

class LeadTemplate(models.Model):
    _inherit = "crm.lead"

    # Custom fields added to lead form view
    language = fields.Many2one("res.lang", string="Language")
    priority1 = fields.Selection([
        ('0', 'Cold'),
        ('1', 'Warm'),
        ('2', 'Hot'),
    ], string='Priority', required=True)
    pipeline_ids = fields.Many2many("pipeline.master", string="Select Opportunity", required=True)
    contact_name2 = fields.Char(string="Contact Name 2")
    mobile2 = fields.Char(string="Mobile 2")
    create_date = fields.Datetime(string="Date", readonly=False)
    call_type = fields.Selection([
        ('daily_call', 'Daily Call'),
        ('existing_customer', 'Existing Customer'),
    ], string='Call Type')

    # Custom fields added for BD and Sales weekly report generation
    source_ids = fields.Many2many("prospect.source", string="Source of Prospect")
    is_decision_maker_identified = fields.Boolean(string="Decision maker Identified")
    is_decision_maker_contacted = fields.Boolean(string="Decision maker Contacted")
    qualification_date = fields.Datetime("Qualification Date", readonly=True)
    date_conversion = fields.Date(string="Opportunity Date", help="Date when lead was converted to opportunity")

class PipelineMaster(models.Model):
    _name = "pipeline.master"
    _description = "Pipeline Master"
    _inherit = ['mail.thread']
    _rec_name = "pipeline"

    pipeline = fields.Char(string="Name")

class ProspectSource(models.Model):
    _name = "prospect.source"
    _description = "Source of prospect"
    _inherit = ['mail.thread']
    _rec_name = "source"

    source = fields.Char(string="Name")
    
class CombinedWeeklyReportWizard(models.TransientModel):
    _name = 'combinedweekly.report.wizard'
    _description = 'Combined Weekly Activity Tracker Report Wizard'

    salesperson_id = fields.Many2one('res.users', string="Salesperson", required=True)
    
    file_data = fields.Binary('Report File')
    file_name = fields.Char('File Name')

    def action_print_combined_report(self):
        """ Generate and download Excel report with BD & Sales report in different sheets """

        salesperson = self.salesperson_id
        leads = self.env['crm.lead'].search([('user_id', '=', salesperson.id), ('active', 'in', [True, False])])

        # Create Excel workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        bd_sheet = workbook.add_worksheet('BD Weekly Activity Tracker Report')
        sales_sheet = workbook.add_worksheet('Sales Weekly Activity Tracker Report')

        ###############################**BD Weekly Activity Report Sheet**####################################
        
        # Set column widths (B to Q)
        column_widths = [18] * 16  # 16 columns from B to Q
        for i, width in enumerate(column_widths, start=1):  # Start from column B (index 1)
            bd_sheet.set_column(i, i, width)

        # Define Formats
        title_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 18, 'border': 1
        })
        bold_format = workbook.add_format({'bold': True, 'font_size': 12, 'valign': 'vcenter', 'border': 1})
        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'text_wrap': True, 'bg_color': '#DEEBF7', 'border': 1
        })
        text_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter','border': 1, 'text_wrap': True
        })
        date_format = workbook.add_format({
            'num_format': 'dd-mm-yyyy', 'align': 'center', 'valign': 'vcenter', 'border': 1
        })

        # Merge and Center Title (B2:B4 to Q2:Q4)
        bd_sheet.merge_range('B2:Q4', "Biz Development Weekly Activity Tracker", title_format)
        
        # Add Logos (Adjust paths accordingly)
        logo_left_path = '/odoo17/custom/addons/microaccess/static/logo_left.png'
        logo_right_path = '/odoo17/custom/addons/microaccess/static/logo_right.png'

        if logo_left_path:
            bd_sheet.insert_image('D2', logo_left_path, {'x_scale': 1.0, 'y_scale': 1.0 })

        if logo_right_path:
            bd_sheet.insert_image('P2', logo_right_path, {'x_scale': 0.6, 'y_scale': 0.6, 'y_offset': 5 })

        # Merge and Center Team Member Name (B5 to Q5)
        bd_sheet.merge_range('B5:Q5', f"Team Member Name: {salesperson.name}", bold_format)
        bd_sheet.set_row(4, 40)

        # Headers (Within B to Q)
        headers = [
            'Date', 'Week Number', 'Company Name', 'Contact Person', 'Decision Maker Identified',
            'Decision Maker Contacted', 'Source of Prospect', 'Current Stage', 'Date of Last Contact',
            'Type of Last Contact', 'Prospect Identification Date', 'First Contact Date',
            'Qualification Date', 'Closure Date', 'Expected Closure Date', 'Remarks / Comments'
        ]

        header_row = 6  # Adjusted to match merged title & team name
        
        # Write Headers & Adjust Row Height Based on Content
        for col, header in enumerate(headers, start=1):  # Start from column B
            bd_sheet.write(header_row, col, header, header_format)
            bd_sheet.set_row(header_row, 38)  # Adjust row height to fit wrapped text

        # Enable Filters (For Columns B to Q)
        bd_sheet.autofilter(header_row, 1, header_row, len(headers))

        # Write Data (Within B to Q, Wrapping Enabled)
        row = header_row + 1
        for lead in leads:
            week_number = lead.create_date.strftime('%U') if lead.create_date else ''
            decision_maker_identified = 'Yes' if lead.is_decision_maker_identified else 'No'
            decision_maker_contacted = 'Yes' if lead.is_decision_maker_contacted else 'No'

            bd_sheet.write(row, 1, lead.create_date.strftime('%d-%m-%Y') if lead.create_date else "", date_format)
            bd_sheet.write(row, 2, week_number, text_format)
            bd_sheet.write(row, 3, lead.partner_id.name or "", text_format)
            bd_sheet.write(row, 4, lead.contact_name or "", text_format)
            bd_sheet.write(row, 5, decision_maker_identified, text_format)
            bd_sheet.write(row, 6, decision_maker_contacted, text_format)
            bd_sheet.write(row, 7, lead.source_ids.source or "", text_format)
            bd_sheet.write(row, 8, lead.stage_id.name or "", text_format)
            bd_sheet.write(row, 9, lead.date_last_stage_update.strftime('%d-%m-%Y') if lead.date_last_stage_update else "", date_format)
            bd_sheet.write(row, 10,lead.call_type or "", text_format)

            # Prospect Identification date (when the source of prospect was defined)
            prospect_identification_date = ""
            if lead.source_ids:
                source_dates = lead.source_ids.mapped('create_date')  # Assuming 'create_date' is when the source was added
                if source_dates:
                    prospect_identification_date = min(source_dates).strftime('%d-%m-%Y')
            bd_sheet.write(row, 11, prospect_identification_date, date_format) 

            # First Contact Date (When the Lead was Created)
            first_contact_date = lead.create_date.strftime('%d-%m-%Y') if lead.create_date else ""
            bd_sheet.write(row, 12, first_contact_date, date_format)

            # Ensure Qualification Date is Retained Once Set(When the lead was moved from New to Qualified stage)
            if not lead.qualification_date and lead.stage_id.name.lower() == "qualified":
                lead.qualification_date = lead.date_last_stage_update  # Save it permanently in the DB

            qualification_date = lead.qualification_date.strftime('%d-%m-%Y') if lead.qualification_date else ""
            bd_sheet.write(row, 13, qualification_date, date_format)

            # Set Closure Date (When the lead was Won/Lost)
            closure_date = lead.date_closed.strftime('%d-%m-%Y') if lead.stage_id.is_won and lead.date_closed else (
                lead.date_last_stage_update.strftime('%d-%m-%Y') if not lead.active and lead.date_last_stage_update else ""
            )
            bd_sheet.write(row, 14, closure_date, date_format)

            bd_sheet.write(row, 15, lead.date_deadline.strftime('%d-%m-%Y') if lead.date_deadline else "", date_format)

            # Set Remarks
            if lead.stage_id.is_won:
                remarks = "Won"
            elif not lead.active and lead.lost_reason_id:
               remarks = f"Lost - {lead.lost_reason_id.name}" 
            else:
                remarks = lead.description or ""
            bd_sheet.write(row, 16, remarks, text_format)

            # Auto-adjust row height for text wrapping
            bd_sheet.set_row(row, 30)

            row += 1

        ###############################**Sales Weekly Activity Report Sheet**####################################

        # Set column widths (B to Q)
        column_widths = [18] * 14  # 14 columns from B to O
        for i, width in enumerate(column_widths, start=1):  # Start from column B (index 1)
            sales_sheet.set_column(i, i, width)

        # Define Formats
        title_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 18, 'border': 1
        })
        bold_format = workbook.add_format({'bold': True, 'font_size': 12,'valign': 'vcenter','border': 1})
        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'text_wrap': True, 'bg_color': '#DEEBF7', 'border': 1
        })
        text_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True
        })
        date_format = workbook.add_format({
            'num_format': 'dd-mm-yyyy', 'align': 'center', 'valign': 'vcenter', 'border': 1
        })

        # Merge and Center Title (B2:B4 to Q2:Q4)
        sales_sheet.merge_range('B2:O4', "Sales Weekly Activity Tracker", title_format)

        # Add Logos (Adjust paths accordingly)
        logo_left_path = '/odoo17/custom/addons/microaccess/static/logo_left.png'
        logo_right_path = '/odoo17/custom/addons/microaccess/static/logo_right.png'

        if logo_left_path:
            sales_sheet.insert_image('D2', logo_left_path, {'x_scale': 1.0, 'y_scale': 1.0})

        if logo_right_path:
            sales_sheet.insert_image('N2', logo_right_path, {'x_scale': 0.6, 'y_scale': 0.6, 'y_offset': 5})

        # Merge and Center Team Member Name (B5 to Q5)
        sales_sheet.merge_range('B5:O5', f"Team Member Name: {salesperson.name}", bold_format)
        sales_sheet.set_row(4, 40)

        # Headers (Within B to Q)
        headers = [
            'Date', 'Week Number', 'Company Name', 'Contact Person', 'Source of Prospect', 'Current Stage', 'Quoted Value', 
            'Date of Last Contact','Type of Last Contact', 'Opportunity Date',
            'Hotlist Date', 'Closure Date', 'Expected Closure Date', 'Remarks / Comments'
        ]

        header_row = 6  # Adjusted to match merged title & team name

        # Write Headers & Adjust Row Height Based on Content
        for col, header in enumerate(headers, start=1):  # Start from column B
            sales_sheet.write(header_row, col, header, header_format)
            sales_sheet.set_row(header_row, 38)  # Adjust row height to fit wrapped text

        # Enable Filters (For Columns B to O)
        sales_sheet.autofilter(header_row, 1, header_row, len(headers))

        # Write Data (Within B to O, Wrapping Enabled)
        row = header_row + 1
        for lead in leads.filtered(lambda l: l.type == 'opportunity'): # Filter set to generate reports of only those lead records which are converted to opportunity
            week_number = lead.create_date.strftime('%U') if lead.create_date else ''
            quoted_value = lead.expected_revenue or 0.0

            # Set Opportunity Date (Date of Conversion: when daily call was converted to opportunity)
            opportunity_date = lead.date_conversion.strftime('%d-%m-%Y') if hasattr(lead, "date_conversion") and lead.date_conversion else ''

            # Set Hotlist Date (When Priority is Marked as Hotlist)
            hotlist_date = ""
            if lead.priority1 == '2' and lead.write_date:
                hotlist_date = lead.write_date.strftime('%d-%m-%Y')  # Using last modification date

            sales_sheet.write(row, 1, lead.create_date.strftime('%d-%m-%Y') if lead.create_date else "", date_format)
            sales_sheet.write(row, 2, week_number, text_format)
            sales_sheet.write(row, 3, lead.partner_id.name or "", text_format)
            sales_sheet.write(row, 4, lead.contact_name or "", text_format)
            sales_sheet.write(row, 5, lead.source_ids.source or "", text_format)
            sales_sheet.write(row, 6, lead.stage_id.name or "", text_format)
            sales_sheet.write(row, 7, quoted_value, text_format)
            sales_sheet.write(row, 8, lead.date_last_stage_update.strftime('%d-%m-%Y') if lead.date_last_stage_update else "", date_format)
            sales_sheet.write(row, 9, lead.call_type or "", text_format)
            sales_sheet.write(row, 10, opportunity_date, date_format)
            sales_sheet.write(row, 11, hotlist_date, date_format)

            # Set Closure Date (When lead is Won/Lost)
            closure_date = lead.date_closed.strftime('%d-%m-%Y') if lead.stage_id.is_won and lead.date_closed else (
                lead.date_last_stage_update.strftime('%d-%m-%Y') if not lead.active and lead.date_last_stage_update else ""
            )
            sales_sheet.write(row, 12, closure_date, date_format)

            sales_sheet.write(row, 13, lead.date_deadline.strftime('%d-%m-%Y') if lead.date_deadline else "", date_format)

            # Set Remarks
            if lead.stage_id.is_won:
                remarks = "Won"
            elif not lead.active and lead.lost_reason_id:
                remarks = f"Lost - {lead.lost_reason_id.name}" 
            else:
                remarks = lead.description or ""

            sales_sheet.write(row, 14, remarks, text_format)

            # Auto-adjust row height for text wrapping
            sales_sheet.set_row(row, 30)

            row += 1
        
        # Close workbook
        workbook.close()
        output.seek(0)

        # Convert file to binary
        file_data = base64.b64encode(output.read())
        file_name = f'{salesperson.name}_BD & Sales Review.xlsx'
        output.close()

        # Save file to wizard and return download action
        self.write({'file_data': file_data, 'file_name': file_name})

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=combinedweekly.report.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }
