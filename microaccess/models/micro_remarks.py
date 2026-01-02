from odoo import fields, models, api

class MicroRemarks(models.Model):
    _name = 'micro.remarks'
    _description = 'Micro Remarks' 
    _inherit=['mail.thread']
    

    name= fields.Char(string='Remarks', tracking=True)