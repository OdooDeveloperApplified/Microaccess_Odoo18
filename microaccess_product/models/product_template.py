from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Code to open wizards for blocking quantity
    def action_open_blocked_quantity(self):
        """Open wizard to block quantity for the product."""
        self.ensure_one()
        return {
            'name': 'Block Quantity',
            'type': 'ir.actions.act_window',
            'res_model': 'block.quantity.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('microaccess_product.view_block_quantity_wizard_form').id,
            'target': 'new',
            'context': {'default_product_id': self.product_variant_id.id},
        } 
    
    # Code to open wizards for unblocking quantity
    def action_open_unblocked_quantity(self):
        """Open wizard to unblock quantity for the product."""
        self.ensure_one()
        return {
            'name': 'Unblock Quantity',
            'type': 'ir.actions.act_window',
            'res_model': 'unblock.quantity.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('microaccess_product.view_unblock_quantity_wizard_form').id,
            'target': 'new',
            'context': {'default_product_id': self.product_variant_id.id},
        } 

    blocked_quantity = fields.Float(
        string="Blocked Quantity",
        compute="_compute_blocked_quantity",
        store=False, 
    )

    unblocked_quantity = fields.Float(
        string="Unblocked Quantity",
        compute="_compute_unblocked_quantity",
        store=False,  
    )

    # Code to compute blocked quantity (recently moved from Stock to Blocked location)
    @api.depends('product_variant_ids.stock_quant_ids.quantity', 'product_variant_ids.stock_quant_ids.location_id')
    def _compute_blocked_quantity(self):
        """Compute total quantity in Blocked Quantity Goods location for all variants."""
        blocked_location = self.env.ref('microaccess_product.stock_location_quantity_blocked', raise_if_not_found=False)
        for product in self:
            if blocked_location:
                quants = self.env['stock.quant'].search([
                    ('product_id', 'in', product.product_variant_ids.ids),
                    ('location_id', '=', blocked_location.id)
                ])
                product.blocked_quantity = sum(quants.mapped('quantity'))
            else:
                product.blocked_quantity = 0

    # Code to compute unblocked quantity (recently moved from Blocked location to Stock)
    @api.depends('product_variant_ids.stock_quant_ids.quantity', 'product_variant_ids.stock_move_ids.state')
    def _compute_unblocked_quantity(self):
        """Compute quantity recently unblocked from Blocked location to Stock."""
        blocked_location = self.env.ref('microaccess_product.stock_location_quantity_blocked', raise_if_not_found=False)
        stock_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        
        for product in self:
            if not blocked_location or not stock_location:
                product.unblocked_quantity = 0
                continue

            # Find the latest validated picking that moved stock from Blocked -> Stock for this product
            last_move = self.env['stock.move'].search([
                ('product_id', 'in', product.product_variant_ids.ids),
                ('state', '=', 'done'),
                ('location_id', '=', blocked_location.id),
                ('location_dest_id', '=', stock_location.id),
            ], order='date desc', limit=1)

            product.unblocked_quantity = last_move.product_uom_qty if last_move else 0

    # Code to view blocked quantity moves by clicking on the blocked quantity stat button
    def action_view_blocked_quantity(self):
        """Open tree view of blocked quants for this product."""
        self.ensure_one()
        blocked_location = self.env.ref('microaccess_product.stock_location_quantity_blocked')
        stock_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        moves = self.env['stock.move'].search([
            ('product_id', 'in', self.product_variant_ids.ids),
            ('state', '=', 'done'),
            ('location_id', '=', stock_location.id),
            ('location_dest_id', '=', blocked_location.id),
            
        ])
        return {
            'name': _('Blocked Quantity Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('microaccess_product.view_blocked_quantity_tree').id, 'list')],
            'domain': [('id', 'in', moves.ids)],
            'target': 'current',
        }
    
    # Code to view unblocked quantity moves by clicking on the unblocked quantity stat button
    def action_view_unblocked_quantity(self):
        """Open tree view of unblocked quantities (moves from Blocked -> Stock)."""
        self.ensure_one()
        unblocked_location = self.env.ref('microaccess_product.stock_location_quantity_blocked')
        stock_location = self.env.ref('stock.stock_location_stock')

        # Find all confirmed moves from Blocked -> Stock for this product
        moves = self.env['stock.move'].search([
            ('product_id', 'in', self.product_variant_ids.ids),
            ('state', '=', 'done'),
            ('location_id', '=', unblocked_location.id),
            ('location_dest_id', '=', stock_location.id),
        ])

        return {
            'name': _('Unblocked Quantity Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('microaccess_product.view_unblocked_quantity_tree').id, 'list')],
            'domain': [('id', 'in', moves.ids)],
            'target': 'current',
        }

class BlockQuantityWizard(models.TransientModel):
    _name = "block.quantity.wizard"
    _description = "Block Product Quantity Wizard"

    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float(string="Quantity to Block", required=True)
    source_location_id = fields.Many2one(
        'stock.location', string="Source Location",
        default=lambda self: self.env.ref('stock.stock_location_stock'),
        required=True
    )

    blocked_location_id = fields.Many2one(
        'stock.location', string="Blocked Location",
        default=lambda self: self.env.ref('microaccess_product.stock_location_quantity_blocked'),
        required=True
    )

    # Code to confirm blocking quantity and related stock moves
    def action_confirm_block(self):
        """Move stock from source to blocked location."""
        self.ensure_one()
        product = self.product_id
        qty = self.quantity

        if qty <= 0:
            raise UserError("Quantity must be greater than zero.")

        # Check available stock in source location
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', self.source_location_id.id),
        ])
        available_qty = sum(quants.mapped('quantity'))

        if qty > available_qty:
            raise UserError(f"Not enough stock in {self.source_location_id.name}. Available: {available_qty}")

        # Create internal transfer (stock picking)
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,  # Internal transfer
            'location_id': self.source_location_id.id,
            'location_dest_id': self.blocked_location_id.id,
            'move_type': 'direct',
        })

        # Create move line
        self.env['stock.move'].create({
            'name': f"Block {product.display_name}",
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.blocked_location_id.id,
        })

        # Confirm and assign picking
        picking.action_confirm()
        # 
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
    
        # Validate picking (done)
        picking.button_validate()

        # Recompute blocked_quantity dynamically
        product.product_tmpl_id._compute_blocked_quantity()

        return {'type': 'ir.actions.act_window_close'}

class UnblockQuantityWizard(models.TransientModel):
    _name = "unblock.quantity.wizard"
    _description = "Unblock Product Quantity Wizard"

    product_id = fields.Many2one('product.product', string="Product", required=True)
    quantity = fields.Float(string="Quantity to Unblock", required=True)
    source_location_id = fields.Many2one(
        'stock.location', string="Source Location",
        default=lambda self: self.env.ref('microaccess_product.stock_location_quantity_blocked'),
        required=True
    )

    # Destination is stock location because we are moving back TO stock
    stock_location_id = fields.Many2one(
        'stock.location', string="Stock Location",
        default=lambda self: self.env.ref('stock.stock_location_stock'),
        required=True
    )

    # Code to confirm unblocking quantity and related stock moves
    def action_confirm_unblock(self):
        """Move stock from blocked location back to stock location."""
        self.ensure_one()
        product = self.product_id
        qty = self.quantity

        if qty <= 0:
            raise UserError("Quantity must be greater than zero.")

        # Check available stock in BLOCKED location
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', self.source_location_id.id),
        ])
        available_qty = sum(quants.mapped('quantity'))

        if qty > available_qty:
            raise UserError(f"Not enough blocked stock in {self.source_location_id.name}. Available: {available_qty}")

        # Create internal picking to move stock FROM Blocked -> Stock
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,  # Internal transfer
            'location_id': self.source_location_id.id,  # FROM Blocked
            'location_dest_id': self.stock_location_id.id,  # TO Stock
            'move_type': 'direct',
        })

        # Create move line
        self.env['stock.move'].create({
            'name': f"Unblock {product.display_name}",
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.stock_location_id.id,
        })

        # Confirm, assign and validate picking
        picking.action_confirm()
        # 
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

        # Recompute quantities dynamically
        product.product_tmpl_id._compute_blocked_quantity()
        product.product_tmpl_id._compute_unblocked_quantity()

        # Pass last unblocked qty via context
        return {
            'type': 'ir.actions.act_window_close',
            'context': {
                'last_unblocked_qty': qty,
                'last_unblocked_product_id': product.id
            }
        }
