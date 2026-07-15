{
    'name': 'DTB Till Moja Integration',
    'summary': """
        DTB Till Moja - M-Pesa payment processing, reference validation,
        and automated invoice reconciliation for Odoo clinics.
    """,
    'description': """
        DTB Till Moja Payments Integration
        ====================================
        Integrates Diamond Trust Bank (Kenya) Till Moja payment platform
        with Odoo for automated M-Pesa payment processing.

        Key Features:
        1. Till Configuration: Manage DTB Till credentials per company/branch.
        2. Reference Validation: Pre-payment invoice verification endpoint.
        3. Payment Callback: Inbound webhook to process settled payments.
        4. Auto-Reconciliation: Match incoming payments to invoices and post.
        5. Mismatch Queue: Manual reconciliation for unmatched transactions.

        Dependencies:
        - base, account, payment: Standard Odoo financial modules
    """,
    'author': 'Mobipine Limited',
    'website': 'https://www.mobipine.com',
    'category': 'Accounting/Payments',
    'version': '19.0.1.0.0',
    'depends': [
        'base',
        'account',
        'payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
        'views/dtb_till_views.xml',
        'views/dtb_transaction_views.xml',
        'wizard/dtb_stk_wizard_views.xml',
        'views/dtb_invoice_view.xml',
    ],
    'external_dependencies': {
        'python': [],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
