from app.repositories import ExpenseRepository, PaymentRepository
import sys

def main(start: str, end: str, org_id: int):
    exp_repo = ExpenseRepository()
    pay_repo = PaymentRepository()

    print(f"Report window: {start} .. {end} (org_id={org_id})\n")
    print("Expenses by category:")
    for row in exp_repo.sum_by_category(org_id, start, end):
        print(row)

    print("\nPayments by type:")
    for row in pay_repo.sum_by_type(org_id, start, end):
        print(row)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/run_report.py YYYY-MM-DD YYYY-MM-DD ORG_ID")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))