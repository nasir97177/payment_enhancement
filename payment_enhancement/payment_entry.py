# import frappe

# def allow_flexible_payment_entry(doc, method):
#     """
#     Payment Entry Hook:
#     - Works for Employee, Supplier, Customer
#     - Uses the Paid From / Paid To already set in the document
#     - Does not throw errors for missing party accounts
#     - Syncs amounts automatically
#     """
#     # Only handle Employee, Supplier, Customer
#     if doc.party_type not in ("Employee", "Supplier", "Customer"):
#         return

#     # Ensure Payment Type is valid
#     if doc.payment_type not in ("Pay", "Receive"):
#         frappe.throw("Payment Type must be either 'Pay' or 'Receive'.")

#     # Only assign Paid From / Paid To if they are already empty
#     if doc.payment_type == "Receive":
#         if not doc.paid_from:
#             doc.paid_from = None  # keep None if not set
#         if not doc.paid_to:
#             doc.paid_to = None
#     else:  # Pay
#         if not doc.paid_from:
#             doc.paid_from = None
#         if not doc.paid_to:
#             doc.paid_to = None

#     # Sync amounts safely
#     if doc.payment_type == "Receive":
#         doc.received_amount = doc.received_amount or doc.paid_amount or 0
#     else:
#         doc.paid_amount = doc.paid_amount or doc.received_amount or 0

#     # Recompute internal fields safely
#     try:
#         if hasattr(doc, "set_missing_values"):
#             doc.set_missing_values()
#         if hasattr(doc, "set_exchange_rate"):
#             doc.set_exchange_rate()
#         if hasattr(doc, "set_amounts"):
#             doc.set_amounts()
#         if hasattr(doc, "set_difference_amount"):
#             doc.set_difference_amount()
#     except Exception:
#         pass


import frappe

def allow_flexible_payment_entry(doc, method):
    """
    Flexible Payment Entry Hook for ERPNext:
    - Handles Employee, Supplier, Customer payments
    - Skips 'Party Type mandatory' or 'Invalid Party for Account' errors
    - Detects Cash/Bank vs Receivable/Payable accounts automatically
    """

    # Valid party types only
    allowed_party_types = ("Employee", "Supplier", "Customer")

    # Ensure payment type is correct
    if doc.payment_type not in ("Pay", "Receive"):
        frappe.throw("Payment Type must be either 'Pay' or 'Receive'.")

    # Helper: check account type
    def get_account_type(account):
        if not account:
            return None
        return frappe.db.get_value("Account", account, "account_type")

    # Detect Paid From / Paid To account types
    paid_from_type = get_account_type(doc.paid_from)
    paid_to_type = get_account_type(doc.paid_to)

    if doc.payment_type == "Receive":
        # If to Cash/Bank → no party needed
        if paid_to_type in ("Cash", "Bank"):
            doc.party_type = None
            doc.party = None
        # If to Receivable → ensure party fields exist
        elif paid_to_type == "Receivable":
            if not doc.party_type:
                doc.party_type = "Customer"
            if not doc.party:
                frappe.throw("Party is mandatory for Receivable accounts.")
        doc.received_amount = doc.received_amount or doc.paid_amount or 0
        doc.paid_amount = doc.paid_amount or doc.received_amount or 0


    elif doc.payment_type == "Pay":
        # If from Cash/Bank → no party needed
        if paid_from_type in ("Cash", "Bank"):
            doc.party_type = None
            doc.party = None
        # If from Payable → ensure party fields exist
        elif paid_from_type == "Payable":
            if not doc.party_type:
                # Guess party type if not provided
                if frappe.db.exists("Supplier", getattr(doc, "party", None)):
                    doc.party_type = "Supplier"
                elif frappe.db.exists("Employee", getattr(doc, "party", None)):
                    doc.party_type = "Employee"
                else:
                    doc.party_type = "Supplier"
            if not doc.party:
                frappe.throw("Party is mandatory for Payable accounts.")
        doc.paid_amount = doc.paid_amount or doc.received_amount or 0
        doc.received_amount = doc.received_amount or doc.paid_amount or 0


    for fn in (
        "set_missing_values",
        "set_exchange_rate",
        "set_amounts",
        "set_difference_amount",
    ):
        if hasattr(doc, fn):
            try:
                getattr(doc, fn)()
            except Exception:
                pass
