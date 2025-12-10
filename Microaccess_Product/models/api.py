import xmlrpc.client

# Odoo connection details
url = 'http://181.214.44.28:8019'
db = 'ma_18_ent'
username = 'ma_18_ent'
password = 'ma_18_ent'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
if not uid:
    print("Authentication Failed")
    exit()

print("Authentication Success")
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Helper function to get UoM ID by name
def get_uom_id(uom_name):
    uom_ids = models.execute_kw(
        db, uid, password,
        'uom.uom', 'search',
        [[['name', '=', uom_name]]],
        {'limit': 1}
    )
    return uom_ids[0] if uom_ids else None

units_uom_id = get_uom_id('Units')
nos_uom_id = get_uom_id('Nos.')

if not units_uom_id or not nos_uom_id:
    print("UoM 'Units' or 'Nos.' not found!")
    exit()

print(f"Units UoM ID: {units_uom_id}, Nos. UoM ID: {nos_uom_id}")

# Search all products with UoM = Units
product_ids = models.execute_kw(
    db, uid, password,
    'product.product', 'search',
    [[['uom_id', '=', units_uom_id]]]
)
print(f"Found {len(product_ids)} products with UoM 'Units'")

# Filter products that have no stock moves, no sale order lines, no purchase order lines
safe_product_ids = []
for pid in product_ids:
    has_move = models.execute_kw(db, uid, password, 'stock.move', 'search', [[['product_id','=',pid]]], {'limit':1})
    has_soline = models.execute_kw(db, uid, password, 'sale.order.line', 'search', [[['product_id','=',pid]]], {'limit':1})
    has_poline = models.execute_kw(db, uid, password, 'purchase.order.line', 'search', [[['product_id','=',pid]]], {'limit':1})

    if not (has_move or has_soline or has_poline):
        safe_product_ids.append(pid)

print(f"Products safe to update: {len(safe_product_ids)}")

# Update safe products
if safe_product_ids:
    result = models.execute_kw(
        db, uid, password,
        'product.product', 'write',
        [safe_product_ids, {'uom_id': nos_uom_id, 'uom_po_id': nos_uom_id}]
    )
    print(f"Products updated successfully: {result}")
else:
    print("No products safe to update.")
