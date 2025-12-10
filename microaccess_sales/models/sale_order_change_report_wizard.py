# models/sale_order_change_report_wizard.py
from odoo import models, fields, api
from io import BytesIO
import xlsxwriter
import base64
from datetime import datetime
from odoo.tools import html2plaintext 
from odoo.modules.module import get_module_resource
import os

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    

    price_unit = fields.Float(
        string="Unit Price",
        compute='_compute_price_unit',
        digits='Product Price',
        store=True, readonly=False, required=True, precompute=True, tracking=True)
    
    def write(self, vals):
        if 'price_unit' in vals:
            for line in self:
                old_price = line.price_unit
                new_price = vals['price_unit']
                if old_price != new_price:
                    msg = f"Unit Price changed for line '{line.name}': {old_price} → {new_price}"
                    line.order_id.message_post(body=msg)
        return super().write(vals)
    
    @api.model
    def create(self, vals):
        line = super().create(vals)
        if 'price_unit' in vals and 'order_id' in vals:
            product = line.product_id.display_name or 'Unknown Product'
            price = vals['price_unit']
            msg = f"Unit Price set for new line '{product}': {price}"
            line.order_id.message_post(body=msg)
        return line

class SaleOrderChangeReportWizard(models.TransientModel):
    _name = 'sale.order.change.report.wizard'
    _description = 'Sale Order Change Report Wizard'

    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)
    file_data = fields.Binary('Excel File', readonly=True)
    file_name = fields.Char('File Name', readonly=True)

    def action_generate_excel_report(self):
        orders = self.env['sale.order'].search([
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
            ('state', '=', 'sale')
        ])
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Change Report")
        
        column_widths = [18,18,18,18,18,50]  # 16 columns from B to Q
        for i, width in enumerate(column_widths, start=1):  # Start from column B (index 1)
            worksheet.set_column(i, i, width)

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
        body_format = workbook.add_format({ 'align': 'left', 'valign': 'vcenter','border': 1, 'text_wrap': True})

        # Merge and Center Title (B2:B4 to Q2:Q4)
        worksheet.merge_range('B2:G4', "After Sale Order Confirmation Changes", title_format)
        
        # Add Logos (Adjust paths accordingly)
        # logo_left_path = '/odoo18/custom/addons/microaccess_sales/static/logo_left.png'
        # logo_right_path = '/odoo18/custom/addons/microaccess_sales/static/logo_right.png'
        logo_left_path = get_module_resource('Microaccess_CRM', 'static', 'logo_left.png')
        logo_right_path = get_module_resource('Microaccess_CRM', 'static', 'logo_right.png')

        if logo_left_path and os.path.exists(logo_left_path):
            worksheet.insert_image('B2', logo_left_path, {'x_scale': 1.0, 'y_scale': 1.0, 'x_offset':50})

        if logo_right_path and os.path.exists(logo_left_path):
            worksheet.insert_image('G2', logo_right_path,  {'x_scale': 0.6,
        'y_scale': 0.6,
        'x_offset': 200,   # Adjust this value if needed
        'y_offset': 10,
        'positioning': 1  # Absolute positioning
        })

        # Merge and Center Team Member Name (B5 to Q5)
        # worksheet.merge_range('B5:Q5', f"Team Member Name: {salesperson.name}", bold_format)
        # worksheet.set_row(4, 40)

        # Headers (Within B to Q)
        headers = ['Order', 'Customer', 'Order Date', 'Change Date', 'User', 'Details']

        header_row = 6  # Adjusted to match merged title & team name
        
        # Write Headers & Adjust Row Height Based on Content
        for col, header in enumerate(headers, start=1):  # Start from column B
            worksheet.write(header_row, col, header, header_format)
            worksheet.set_row(header_row, 38)  # Adjust row height to fit wrapped text

        # Enable Filters (For Columns B to Q)
        worksheet.autofilter(header_row, 1, header_row, len(headers))
        row = header_row + 1

        headers = ['Order', 'Customer', 'Order Date', 'Change Date', 'User', 'Details']
        for order in orders:
            messages = self.env['mail.message'].sudo().search([
                ('model', '=', 'sale.order'),
                ('res_id', '=', order.id),
            ], order='date asc')

            for msg in messages:
                confirm_date = order.date_order
                if confirm_date and msg.date and msg.date <= confirm_date:
                    continue
                if not msg.body and not msg.tracking_value_ids:
                    continue

                body = ""
                if msg.body:
                   body = html2plaintext(msg.body).strip()
                elif msg.tracking_value_ids:
                    lines = []
                    for tv in msg.tracking_value_ids:
                        if tv.field_id.name in ['amount_total', 'amount_untaxed']:
                            continue
                        field_desc = tv.field_id.field_description or tv.field_id.name
                        old_val = tv.old_value_char or tv.old_value_text or str(tv.old_value_float or '')
                        new_val = tv.new_value_char or tv.new_value_text or str(tv.new_value_float or '')
                        if old_val or new_val:
                            lines.append(f"{field_desc}: {old_val} → {new_val}")
                    body = "\n".join(lines)

                if body:
                    skip_phrases = [
                        "Sales Order created",
                        "Status: Quotation → Sales Order",
                        "Quotation → Sales Order",
                        "Quotation → Order",
                        "has been created",
                    ]
                    if any(phrase in body for phrase in skip_phrases):
                        continue
                    worksheet.write(row, 1, order.name, text_format)
                    worksheet.write(row, 2, order.partner_id.name, text_format)
                    worksheet.write(row, 3, order.date_order.strftime('%d-%m-%Y'), date_format)
                    worksheet.write(row, 4, msg.date.strftime('%d-%m-%Y %H:%M:%S') if msg.date else '', date_format)
                    worksheet.write(row, 5, msg.author_id.name or 'System', text_format)
                    worksheet.write(row, 6, body, body_format)

                    worksheet.set_row(row, 70)
                    row += 1

        workbook.close()
        output.seek(0)

        file_content = output.read()
        file_base64 = base64.b64encode(file_content)
        filename = f'SaleOrderChangeReport_{self.date_from}_{self.date_to}.xlsx'

        self.write({
            'file_data': file_base64,
            'file_name': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=sale.order.change.report.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'new',
        }
