# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


# class ProductChangeQuantity(models.TransientModel):
#     _inherit = "stock.change.product.qty"
#     _description = "Change Product Quantity"

#     def change_product_qty(self):
#             """ Changes the Product Quantity by creating/editing corresponding quant.
#             """
#             warehouse = self.env['stock.warehouse'].search(
#                 [('company_id', '=', self.env.company.id)], limit=1
#             )
#             # Before creating a new quant, the quand `create` method will check if
#             # it exists already. If it does, it'll edit its `inventory_quantity`
#             # instead of create a new one.
#             goods_product = self.env['product.template'].sudo().search([('type', '=', 'consu')])
#             _logger.info("this is goods product %s", goods_product)

#             product_quantity = 5000
#             for goods in goods_product:
#                 _logger.info("this is inventory track true %s",goods)
#                 if goods.is_storable:
#                     self.env['stock.quant'].with_context(inventory_mode=True).create({
#                         'product_id': goods.id,
#                         'location_id': warehouse.lot_stock_id.id,
#                         'inventory_quantity': product_quantity,
#                     })._apply_inventory()
#                 else:
#                     _logger.info("this is no inventoty track %s",goods)
#             return {'type': 'ir.actions.act_window_close'}

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_update_all_goods_quantity(self):
        """Update the Product Quantity for all goods-type (consumable) products."""
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        )
        goods_products = self.env['product.template'].sudo().search([('type', '=', 'consu')])
        _logger.info("Found %s goods-type products", len(goods_products))

        product_quantity = 0

        for goods in goods_products:
            _logger.info("Processing product: %s", goods.name)
            if goods.is_storable:
                quant = self.env['stock.quant'].with_context(inventory_mode=True).create({
                    'product_id': goods.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'inventory_quantity': product_quantity,
                })
                quant._apply_inventory()
            else:
                _logger.warning("Product %s has no variant, skipping.", goods.name)

        _logger.info("Stock quantities updated successfully for all goods products.")
        return True