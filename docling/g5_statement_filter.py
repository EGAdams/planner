#!/usr/bin/env python3
import sys, json, re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict

CURRENCY_RE = re.compile(r"-?\$?\(?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})\s*\)?")
AMOUNT_EXTRACT_RE = re.compile(r"-?\(?\s*([\d,]+\.\d{2})\s*\)?")
DATE_MMDD_RE = re.compile(r"^\s*(\d{2})/(\d{2})\s*$")
CHECK_NUM_RE = re.compile(r"^\s*(\d+)[\w\*]*\s*$")

def clean_amount_to_float(s):
    if s is None:
        return None
    s = s.strip()
    is_neg = s.startswith("(") and s.endswith(")")
    s2 = s.replace("$", "").replace(",", "").replace("(", "").replace(")", "").strip()
    try:
        val = float(s2)
        if is_neg:
            val = -val
        return val
    except:
        m = AMOUNT_EXTRACT_RE.search(s)
        if m:
            val = float(m.group(1).replace(",", ""))
            if is_neg:
                val = -val
            return val
        return None

def parse_markdown_from_docling(raw_text):
    try:
        obj = json.loads(raw_text)
        if isinstance(obj, dict):
            if "markdown" in obj:
                return obj["markdown"]
            if "markdown_preview" in obj:
                return obj["markdown_preview"]
    except Exception:
        pass
    return raw_text

def find_section_indices(lines, startswith_text):
    for i, ln in enumerate(lines):
        if ln.strip().startswith(startswith_text):
            return i
    return -1

def parse_statement_period(lines):
    period_re = re.compile(r"Statement Period Date:\s*([0-9/]+)\s*-\s*([0-9/]+)")
    for ln in lines:
        m = period_re.search(ln)
        if m:
            start_s, end_s = m.group(1), m.group(2)
            start_dt = datetime.strptime(start_s, "%m/%d/%Y")
            end_dt = datetime.strptime(end_s, "%m/%d/%Y")
            return start_dt.date(), end_dt.date()
    return None, None

def parse_account_info(lines):
    account_type = None
    account_number = None
    for ln in lines:
        if ln.startswith("Account Type:"):
            account_type = ln.split(":",1)[1].strip()
        if ln.startswith("Account Number:"):
            account_number = ln.split(":",1)[1].strip()
    return account_type, account_number

def parse_account_summary(lines):
    beg_bal = end_bal = None
    checks_cnt = withdrawals_cnt = deposits_cnt = None
    checks_tot = withdrawals_tot = deposits_tot = None
    for ln in lines:
        if "Beginning Balance" in ln:
            am = CURRENCY_RE.search(ln)
            if am:
                beg_bal = clean_amount_to_float(am.group(0))
        if "Ending Balance" in ln:
            am = CURRENCY_RE.search(ln)
            if am:
                end_bal = clean_amount_to_float(am.group(0))
        if "| Checks" in ln and "Withdrawals" not in ln and "Deposits" not in ln:
            parts = [p.strip() for p in ln.strip().strip("|").split("|")]
            if parts and parts[0]:
                try:
                    checks_cnt = int(parts[0])
                except:
                    pass
            am = CURRENCY_RE.search(ln)
            if am:
                checks_tot = clean_amount_to_float(am.group(0))
        if "Withdrawals / Debits" in ln and ln.strip().startswith("|"):
            parts = [p.strip() for p in ln.strip().strip("|").split("|")]
            if parts and parts[0].isdigit():
                withdrawals_cnt = int(parts[0])
            am = CURRENCY_RE.search(ln)
            if am:
                withdrawals_tot = clean_amount_to_float(am.group(0))
        if "Deposits / Credits" in ln and ln.strip().startswith("|"):
            parts = [p.strip() for p in ln.strip().strip("|").split("|")]
            if parts and parts[0].isdigit():
                deposits_cnt = int(parts[0])
            am = CURRENCY_RE.search(ln)
            if am:
                deposits_tot = clean_amount_to_float(am.group(0))
    return {
        "beginning_balance": beg_bal,
        "ending_balance": end_bal,
        "checks_count": checks_cnt,
        "checks_total": checks_tot,
        "withdrawals_count": withdrawals_cnt,
        "withdrawals_total": withdrawals_tot,
        "deposits_count": deposits_cnt,
        "deposits_total": deposits_tot,
    }

def parse_withdrawals(lines, start_idx):
    items = []
    i = start_idx
    while i < len(lines) and "Date" not in lines[i]:
        i += 1
    i += 1
    while i < len(lines):
        ln = lines[i].strip()
        if not ln.startswith("|"):
            break
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cols) >= 3:
            date_s, amount_s, desc = cols[0], cols[1], cols[2]
            if DATE_MMDD_RE.match(date_s) and amount_s:
                items.append({
                    "date": date_s,
                    "amount": -clean_amount_to_float(amount_s),
                    "description": desc
                })
        i += 1
    return items

def parse_deposits(lines, start_idx):
    items = []
    i = start_idx
    while i < len(lines) and "Date" not in lines[i]:
        i += 1
    i += 1
    while i < len(lines):
        ln = lines[i].strip()
        if not ln.startswith("|"):
            break
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        date_col = None
        if len(cols) >= 4 and DATE_MMDD_RE.match(cols[0] or ""):
            date_col = cols[0]
        elif len(cols) >= 4 and DATE_MMDD_RE.match(cols[3] or ""):
            date_col = cols[3]
        elif len(cols) >= 1 and DATE_MMDD_RE.match(cols[0] or ""):
            date_col = cols[0]
        if date_col is None:
            i += 1
            continue
        amount_s = cols[1] if len(cols) > 1 else ""
        desc = cols[2] if len(cols) > 2 else ""
        if amount_s:
            items.append({
                "date": date_col,
                "amount": clean_amount_to_float(amount_s),
                "description": desc
            })
        i += 1
    return items

def parse_checks(lines, start_idx):
    items = []
    i = start_idx
    while i < len(lines) and "Number" not in lines[i]:
        i += 1
    i += 1
    while i < len(lines):
        ln = lines[i].strip()
        if not ln.startswith("|"):
            break
        cols = [c.strip() for c in ln.strip().strip("|").split("|")]
        def process_triplet(trip):
            if len(trip) < 3:
                return None
            num_raw, date_s, amt_s = trip[0], trip[1], trip[2]
            if not DATE_MMDD_RE.match(date_s or ""):
                return None
            if not amt_s:
                return None
            m = CHECK_NUM_RE.match(num_raw or "")
            number = m.group(1) if m else (num_raw or "")
            return {
                "number": number,
                "date": date_s,
                "amount": -clean_amount_to_float(amt_s)
            }
        for j in range(0, len(cols), 3):
            trip = cols[j:j+3]
            item = process_triplet(trip)
            if item:
                items.append(item)
        i += 1
    return items

def parse_daily_balances(lines, start_idx):
    i = start_idx
    mapping = OrderedDict()
    while i < len(lines):
        while i < len(lines) and lines[i].strip() != "Date":
            i += 1
        if i >= len(lines):
            break
        i += 1
        dates = []
        while i < len(lines) and lines[i].strip() not in ("Amount", "Date", ""):
            token = lines[i].strip()
            if DATE_MMDD_RE.match(token):
                dates.append(token)
            i += 1
        if i >= len(lines) or lines[i].strip() != "Amount":
            continue
        i += 1
        amts = []
        while i < len(lines) and lines[i].strip() not in ("Date", ""):
            token = lines[i].strip()
            if token:
                amt_val = clean_amount_to_float(token)
                if amt_val is not None:
                    amts.append(amt_val)
            i += 1
        for d, a in zip(dates, amts):
            mapping[d] = a
    return mapping

def year_for_mm(month_str, period_start, period_end):
    if period_start and period_end:
        start_year = period_start.year
        end_year = period_end.year
        m = int(month_str)
        if m >= period_start.month:
            return start_year
        else:
            return end_year
    return None

def to_iso(mmdd, period_start, period_end):
    m, d = mmdd.split("/")
    y = year_for_mm(m, period_start, period_end) or (period_start.year if period_start else 1900)
    return f"{y:04d}-{int(m):02d}-{int(d):02d}"

def fmt_money(v):
    if v is None:
        return "—"
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}"

def main():
    if len(sys.argv) > 1:
        raw_text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="ignore")
    else:
        raw_text = sys.stdin.read()

    md = parse_markdown_from_docling(raw_text)
    lines = [ln.rstrip() for ln in md.splitlines()]

    checks_idx = find_section_indices(lines, "| Checks")
    withdrawals_idx = find_section_indices(lines, "| Withdrawals / Debits")
    deposits_idx = find_section_indices(lines, "| Deposits / Credits")
    daily_idx = find_section_indices(lines, "## Daily Balance Summary")

    period_start, period_end = parse_statement_period(lines)
    account_type, account_number = parse_account_info(lines)
    summary = parse_account_summary(lines)

    checks = parse_checks(lines, checks_idx) if checks_idx != -1 else []
    withdrawals = parse_withdrawals(lines, withdrawals_idx) if withdrawals_idx != -1 else []
    deposits = parse_deposits(lines, deposits_idx) if deposits_idx != -1 else []
    daily_balances = parse_daily_balances(lines, daily_idx) if daily_idx != -1 else OrderedDict()

    for lst in (checks, withdrawals, deposits):
        for t in lst:
            t["date_iso"] = to_iso(t["date"], period_start, period_end)

    daily_balances_iso = OrderedDict((to_iso(k, period_start, period_end), v) for k, v in daily_balances.items())

    sum_checks = round(sum(x["amount"] for x in checks), 2)
    sum_withdrawals = round(sum(x["amount"] for x in withdrawals), 2)
    sum_deposits = round(sum(x["amount"] for x in deposits), 2)

    beginning = summary["beginning_balance"]
    ending = summary["ending_balance"]

    computed_ending = None
    recon_ok = None
    if beginning is not None:
        computed_ending = round(beginning + sum_checks + sum_withdrawals + sum_deposits, 2)
        if ending is not None:
            recon_ok = abs(computed_ending - ending) < 0.005

    net_change = round((ending - beginning), 2) if (ending is not None and beginning is not None) else None
    net_from_flows = round(sum_deposits + sum_checks + sum_withdrawals, 2)

    transactions_by_day = defaultdict(float)
    for t in deposits + withdrawals + checks:
        transactions_by_day[t["date_iso"]] += t["amount"]

    computed_daily = OrderedDict()
    if daily_balances_iso:
        sorted_daily_dates = list(daily_balances_iso.keys())
        running_balance = beginning if beginning is not None else None
        all_tx_dates_sorted = sorted(set(t["date_iso"] for t in deposits + withdrawals + checks))
        prev_cutoff_idx = 0
        for target in sorted_daily_dates:
            if running_balance is None:
                break
            while prev_cutoff_idx < len(all_tx_dates_sorted) and all_tx_dates_sorted[prev_cutoff_idx] <= target:
                tx_date = all_tx_dates_sorted[prev_cutoff_idx]
                running_balance = round(running_balance + transactions_by_day[tx_date], 2)
                prev_cutoff_idx += 1
            computed_daily[target] = running_balance

    structured = {
        "account": {
            "type": account_type,
            "number": account_number,
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
        },
        "summary_reported": summary,
        "line_items": {
            "checks": checks,
            "withdrawals": withdrawals,
            "deposits": deposits,
        },
        "totals_from_line_items": {
            "checks": sum_checks,
            "withdrawals": sum_withdrawals,
            "deposits": sum_deposits,
            "net_from_flows": net_from_flows
        },
        "reconciliation": {
            "beginning": beginning,
            "ending_reported": ending,
            "ending_computed_from_line_items": computed_ending,
            "reconciles": bool(recon_ok) if recon_ok is not None else None,
            "ending_minus_beginning": net_change,
            "proof_deposits_minus_outflows": net_from_flows,
            "difference": round((ending - computed_ending), 2) if (ending is not None and computed_ending is not None) else None
        },
        "daily_balances_provided": daily_balances_iso,
        "daily_balances_computed": computed_daily,
        "daily_balance_diffs": {
            d: round(daily_balances_iso[d] - computed_daily.get(d, float('nan')), 2)
            for d in daily_balances_iso.keys() if d in computed_daily
        }
    }

    out_dir = Path(".")
    (out_dir / "statement_structured.json").write_text(json.dumps(structured, indent=2), encoding="utf-8")

    lines_out = []
    lines_out.append("FIFTH THIRD STATEMENT RECONCILIATION REPORT")
    lines_out.append("="*44)
    lines_out.append(f"Account: {account_type or ''}  #{account_number or ''}")
    if period_start and period_end:
        lines_out.append(f"Period: {period_start.isoformat()} to {period_end.isoformat()}")
    lines_out.append("")
    lines_out.append("Reported Summary:")
    lines_out.append(f"  Beginning Balance: {fmt_money(summary['beginning_balance'])}")
    lines_out.append(f"  Checks ({summary['checks_count']}): {fmt_money(summary['checks_total'])}")
    lines_out.append(f"  Withdrawals ({summary['withdrawals_count']}): {fmt_money(summary['withdrawals_total'])}")
    lines_out.append(f"  Deposits ({summary['deposits_count']}): {fmt_money(summary['deposits_total'])}")
    lines_out.append(f"  Ending Balance: {fmt_money(summary['ending_balance'])}")
    lines_out.append("")
    lines_out.append("Line-Item Totals (from parsed tables):")
    lines_out.append(f"  Checks total: {fmt_money(sum_checks)}")
    lines_out.append(f"  Withdrawals total: {fmt_money(sum_withdrawals)}")
    lines_out.append(f"  Deposits total: {fmt_money(sum_deposits)}")
    lines_out.append("")
    lines_out.append("Reconciliation Proof:")
    lines_out.append(f"  Ending (computed) = Beginning + Deposits + Checks + Withdrawals")
    lines_out.append(f"                    = {fmt_money(beginning)} + {fmt_money(sum_deposits)} + {fmt_money(sum_checks)} + {fmt_money(sum_withdrawals)}")
    lines_out.append(f"                    = {fmt_money(computed_ending)}")
    lines_out.append(f"  Ending (reported) = {fmt_money(ending)}")
    ok_text = "OK ✅" if (recon_ok is True) else ("MISMATCH ❌" if recon_ok is False else "UNKNOWN")
    lines_out.append(f"  Match? {ok_text}")
    if ending is not None and computed_ending is not None:
        lines_out.append(f"  Difference (reported - computed): {fmt_money(round(ending - computed_ending,2))}")
    lines_out.append("")
    lines_out.append(f"  Net change from flows = Deposits + Checks + Withdrawals = {fmt_money(net_from_flows)}")
    if structured["reconciliation"]["ending_minus_beginning"] is not None:
        lines_out.append(f"  Net change (Ending - Beginning) = {fmt_money(structured['reconciliation']['ending_minus_beginning'])}")
        lines_out.append(f"  Cross-check match? {'OK ✅' if abs(net_from_flows - structured['reconciliation']['ending_minus_beginning']) < 0.005 else 'MISMATCH ❌'}")
    lines_out.append("")
    if structured["daily_balances_provided"] and structured["daily_balances_computed"]:
        lines_out.append("Daily Balance Verification: (Provided vs. Computed from line items)")
        lines_out.append(f"{'Date':<12}{'Provided':>15}{'Computed':>15}{'Diff':>12}")
        lines_out.append("-"*54)
        for d, provided in structured["daily_balances_provided"].items():
            computed = structured["daily_balances_computed"].get(d)
            diff = None if computed is None else round(provided - computed, 2)
            def fmt(v):
                if v is None: return "—"
                sign = "-" if v < 0 else ""
                return f"{sign}${abs(v):,.2f}"
            lines_out.append(f"{d:<12}{fmt(provided):>15}{fmt(computed):>15}{fmt(diff) if diff is not None else '—':>12}")
        lines_out.append("")
    else:
        lines_out.append("Daily Balance Verification: (insufficient data to compute)")
        lines_out.append("")
    lines_out.append("Appendix: Counts")
    lines_out.append(f"  Checks parsed: {len(checks)}")
    lines_out.append(f"  Withdrawals parsed: {len(withdrawals)}")
    lines_out.append(f"  Deposits parsed: {len(deposits)}")
    lines_out.append("")

    (out_dir / "formatted_report.txt").write_text("\n".join(lines_out), encoding="utf-8")

if __name__ == "__main__":
    main()
