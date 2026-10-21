{
    "name": "Physical Inventory Invoice",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Barcode physical counts and invoice for stock shortages",
    "depends": ["stock", "product", "account", "barcodes"],
    "data": [
        "security/ir.model.access.csv",
        "security/physical_inventory_security.xml",
        "data/physical_inventory_sequence.xml",
        "views/physical_inventory_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}