from app.repositories import (
    OrganizationRepository, ExpenseRepository, PaymentRepository
)
from app.db import query_all
from datetime import date

def print_balances():
    rows = query_all("SELECT * FROM vw_balance_by_org")
    print("\n== Balances ==")
    for r in rows:
        print(f"{r['org_name']}: payments={r['total_payments']:.2f}, expenses={r['total_expenses']:.2f}, net={r['net_balance']:.2f}")

def main():
    orgs = OrganizationRepository()
    expenses = ExpenseRepository()
    payments = PaymentRepository()

    print_balances()

    # Create a new expense for the nonprofit org
    org_np = orgs.list("name=%s", ("GoodWorks Nonprofit",), limit=1)
    if not org_np:
        raise SystemExit("GoodWorks org missing; run scripts/init_db.py first.")
    org_id = org_np[0]['id']

    # Use an existing category (Supplies)
    cat = query_all("SELECT id FROM categories WHERE name=%s AND kind='EXPENSE' LIMIT 1", ("Supplies",))
    cat_id = cat[0]['id']

    print("\nCreating a new expense ...")
    new_id = expenses.insert({
        "org_id": org_id,
        "expense_date": date.today().isoformat(),
        "amount": 42.50,
        "category_id": cat_id,
        "description": "Demo: office supplies",
        "method": "CARD",
    })
    print("Inserted expense id:", new_id)

    # Read it back
    row = expenses.get(new_id)
    print( "new id:", new_id )
    print("Inserted row:", row)

    # Update
    expenses.update(new_id, {"amount": 44.00, "description": "Demo: updated amount"})
    print("Updated row:", expenses.get(new_id))

    # Delete
    expenses.delete(new_id)
    print("Deleted. Exists now?", expenses.get(new_id))

    print_balances()

    # Monthly summaries
    print("\n== Monthly expense summary ==")
    rows = query_all("SELECT * FROM vw_monthly_expense_summary ORDER BY month_start DESC, total_amount DESC LIMIT 10")
    for r in rows:
        print(r)

    print("\n== Monthly payment summary ==")
    rows = query_all("SELECT * FROM vw_monthly_payment_summary ORDER BY month_start DESC, total_amount DESC LIMIT 10")
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()