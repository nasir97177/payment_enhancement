import frappe

def allow_flexible_payment_entry(doc, method):
    """
    Payment Entry Hook:
    - Works for Employee, Supplier, Customer
    - Uses the Paid From / Paid To already set in the document
    - Does not throw errors for missing party accounts
    - Syncs amounts automatically
    """
    # Only handle Employee, Supplier, Customer
    if doc.party_type not in ("Employee", "Supplier", "Customer"):
        return

    # Ensure Payment Type is valid
    if doc.payment_type not in ("Pay", "Receive"):
        frappe.throw("Payment Type must be either 'Pay' or 'Receive'.")

    # Only assign Paid From / Paid To if they are already empty
    if doc.payment_type == "Receive":
        if not doc.paid_from:
            doc.paid_from = None  # keep None if not set
        if not doc.paid_to:
            doc.paid_to = None
    else:  # Pay
        if not doc.paid_from:
            doc.paid_from = None
        if not doc.paid_to:
            doc.paid_to = None

    # Sync amounts safely
    if doc.payment_type == "Receive":
        doc.received_amount = doc.received_amount or doc.paid_amount or 0
    else:
        doc.paid_amount = doc.paid_amount or doc.received_amount or 0

    # Recompute internal fields safely
    try:
        if hasattr(doc, "set_missing_values"):
            doc.set_missing_values()
        if hasattr(doc, "set_exchange_rate"):
            doc.set_exchange_rate()
        if hasattr(doc, "set_amounts"):
            doc.set_amounts()
        if hasattr(doc, "set_difference_amount"):
            doc.set_difference_amount()
    except Exception:
        pass
