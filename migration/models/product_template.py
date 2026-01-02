from odoo import models, fields, api
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    source_record_id = fields.Integer("Source Product ID")

class ProductProduct(models.Model):
    _inherit = "product.product"

    source_record_id = fields.Integer("Source Product-Product ID")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    source_record_id = fields.Integer("Source Partner ID")

class ResPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    source_record_id = fields.Integer(string="Source Partner Category ID")

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    source_record_id = fields.Integer("Source Sale Order ID")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    source_record_id = fields.Integer("Source Sale Order Line ID")

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    source_record_id = fields.Integer("Source Purchase Order ID")

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    source_record_id = fields.Integer("Source Purchase Order Line ID")

class RevisionHistory(models.Model):
    _inherit = 'revision.history'

    source_record_id = fields.Integer("Source Revision ID")

class RevisionHistoryLine(models.Model):
    _inherit = 'revision.history.line'

    source_record_id = fields.Integer("Source Revision Line ID")

class SalesRemarks(models.Model):
    _inherit = "remarks.remarks"

    source_record_id = fields.Integer("Source Remark ID")

class HelpdeskTemplate(models.Model):
    _inherit = "helpdesk.ticket"

    source_record_id = fields.Integer("Source Ticket ID")

class AssignHistory(models.Model):
    _inherit = "assign.history"

    source_record_id = fields.Integer("Source Assign Line ID")

class HoldHistory(models.Model):
    _inherit = "hold.history"

    source_record_id = fields.Integer("Source Hold History ID")

class ReturnableGoods(models.Model):
    _inherit = "returnable.goods"

    source_record_id = fields.Integer("Source Returnable Goods ID")

class RepairOrder(models.Model):
    _inherit = "repair.order"

    source_record_id = fields.Integer("Source Repair Order ID")

class MicroRemarks(models.Model):
    _inherit = 'micro.remarks'

    source_record_id = fields.Integer("Source Micro Remarks ID")

class CEMLead(models.Model):
    _inherit = 'crm.lead'

    source_record_id = fields.Integer("Source CRM Lead ID")