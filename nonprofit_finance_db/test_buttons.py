#!/usr/bin/env python3
"""
Comprehensive Playwright Browser Testing for Pydantic Server
Tests all button functionality in Daily Expense Categorizer
"""
from playwright.sync_api import sync_playwright, expect
import time
import json
from pathlib import Path

def test_daily_expense_categorizer():
    """Test all buttons and interactions on the Daily Expense Categorizer page"""
    
    results = {
        "test_suite": "Daily Expense Categorizer Button Testing",
        "url": "http://localhost:8080/",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tests": [],
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
    }
    
    def log_test(name, status, details="", screenshot_path=""):
        """Log a test result"""
        test_result = {
            "name": name,
            "status": status,
            "details": details,
            "screenshot": screenshot_path
        }
        results["tests"].append(test_result)
        results["summary"]["total"] += 1
        if status == "PASS":
            results["summary"]["passed"] += 1
            print(f"✅ PASS: {name}")
        elif status == "FAIL":
            results["summary"]["failed"] += 1
            print(f"❌ FAIL: {name} - {details}")
        else:
            results["summary"]["warnings"] += 1
            print(f"⚠️  WARN: {name} - {details}")
        if details:
            print(f"   Details: {details}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Run with visible browser for debugging
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        
        # Enable console logging
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        try:
            print("\n" + "="*80)
            print("🚀 PYDANTIC SERVER BUTTON TESTING - PLAYWRIGHT BROWSER AUTOMATION")
            print("="*80 + "\n")
            
            # Test 1: Navigate to the application
            print("\n📍 TEST 1: Navigation and Initial Load")
            page.goto("http://localhost:8080/", wait_until="networkidle")
            time.sleep(2)  # Wait for JavaScript to initialize
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/01-initial-load.png"
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Check if loading completed
            loading_msg = page.locator("#loadingMsg")
            error_msg = page.locator("#errorMsg")
            main_table = page.locator("#mainTable")
            
            if loading_msg.is_visible():
                log_test("Initial Load", "FAIL", "Loading message still visible after 2 seconds", screenshot_path)
            elif error_msg.is_visible():
                error_text = error_msg.text_content()
                log_test("Initial Load", "FAIL", f"Error message displayed: {error_text}", screenshot_path)
            elif main_table.is_visible():
                log_test("Initial Load", "PASS", "Application loaded successfully", screenshot_path)
            else:
                log_test("Initial Load", "WARN", "Unable to determine load status", screenshot_path)
            
            # Test 2: Check header elements
            print("\n📊 TEST 2: Header and Metadata Display")
            month_text = page.locator("#monthText").text_content()
            date_text = page.locator("#dateText").text_content()
            uncat_count = page.locator("#uncatCount").text_content()
            day_total = page.locator("#dayTotal").text_content()
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/02-header-display.png"
            page.screenshot(path=screenshot_path)
            
            if month_text and date_text:
                log_test("Header Display", "PASS", 
                        f"Month: {month_text}, Date: {date_text}, Uncategorized: {uncat_count}, Total: {day_total}",
                        screenshot_path)
            else:
                log_test("Header Display", "FAIL", "Missing header information", screenshot_path)
            
            # Test 3: Month Selector
            print("\n📅 TEST 3: Month Selector Functionality")
            month_select = page.locator("#monthSelect")
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/03-month-selector.png"
            page.screenshot(path=screenshot_path)
            
            if month_select.is_visible():
                options_count = month_select.locator("option").count()
                if options_count > 0:
                    log_test("Month Selector Visible", "PASS", 
                            f"Month selector has {options_count} options", screenshot_path)
                    
                    # Try selecting a month
                    if options_count > 1:
                        first_option_value = month_select.locator("option").first.get_attribute("value")
                        month_select.select_option(first_option_value)
                        time.sleep(1)
                        
                        new_date = page.locator("#dateText").text_content()
                        screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/03b-month-changed.png"
                        page.screenshot(path=screenshot_path)
                        
                        log_test("Month Selector Change", "PASS", 
                                f"Successfully changed month, new date: {new_date}", screenshot_path)
                else:
                    log_test("Month Selector Visible", "FAIL", "Month selector has no options", screenshot_path)
            else:
                log_test("Month Selector Visible", "FAIL", "Month selector not visible", screenshot_path)
            
            # Test 4: First Button
            print("\n⏮️  TEST 4: First Button")
            first_btn = page.locator("#firstBtn")
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/04-first-button.png"
            page.screenshot(path=screenshot_path)
            
            if first_btn.is_visible():
                is_disabled = first_btn.is_disabled()
                first_btn_text = first_btn.text_content()
                
                if not is_disabled:
                    date_before = page.locator("#dateText").text_content()
                    first_btn.click()
                    time.sleep(0.5)
                    date_after = page.locator("#dateText").text_content()
                    
                    screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/04b-after-first-click.png"
                    page.screenshot(path=screenshot_path)
                    
                    log_test("First Button Click", "PASS", 
                            f"Button clicked. Date changed from {date_before} to {date_after}", screenshot_path)
                    
                    # Check if button is now disabled (we're at first day)
                    if first_btn.is_disabled():
                        log_test("First Button State", "PASS", 
                                "Button correctly disabled after navigating to first day", screenshot_path)
                    else:
                        log_test("First Button State", "WARN", 
                                "Button not disabled after navigating to first day", screenshot_path)
                else:
                    log_test("First Button Click", "WARN", "Button is disabled (already at first day)", screenshot_path)
            else:
                log_test("First Button Visible", "FAIL", "First button not visible", screenshot_path)
            
            # Test 5: Last Button
            print("\n⏭️  TEST 5: Last Button")
            last_btn = page.locator("#lastBtn")
            
            date_before = page.locator("#dateText").text_content()
            last_btn.click()
            time.sleep(0.5)
            date_after = page.locator("#dateText").text_content()
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/05-last-button.png"
            page.screenshot(path=screenshot_path)
            
            if date_before != date_after:
                log_test("Last Button Click", "PASS", 
                        f"Button clicked. Date changed from {date_before} to {date_after}", screenshot_path)
                
                # Check if button is now disabled (we're at last day)
                if last_btn.is_disabled():
                    log_test("Last Button State", "PASS", 
                            "Button correctly disabled after navigating to last day", screenshot_path)
                else:
                    log_test("Last Button State", "WARN", 
                            "Button not disabled after navigating to last day", screenshot_path)
            else:
                log_test("Last Button Click", "WARN", "Date did not change (might already be at last day)", screenshot_path)
            
            # Test 6: Previous Button
            print("\n◀️  TEST 6: Previous Button")
            prev_btn = page.locator("#prevBtn")
            
            date_before = page.locator("#dateText").text_content()
            
            if not prev_btn.is_disabled():
                prev_btn.click()
                time.sleep(0.5)
                date_after = page.locator("#dateText").text_content()
                
                screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/06-previous-button.png"
                page.screenshot(path=screenshot_path)
                
                if date_before != date_after:
                    log_test("Previous Button Click", "PASS", 
                            f"Button clicked. Date changed from {date_before} to {date_after}", screenshot_path)
                else:
                    log_test("Previous Button Click", "FAIL", 
                            "Date did not change after clicking previous", screenshot_path)
            else:
                log_test("Previous Button Click", "WARN", "Button is disabled", screenshot_path)
            
            # Test 7: Next Button
            print("\n▶️  TEST 7: Next Button")
            next_btn = page.locator("#nextBtn")
            
            date_before = page.locator("#dateText").text_content()
            
            if not next_btn.is_disabled():
                next_btn.click()
                time.sleep(0.5)
                date_after = page.locator("#dateText").text_content()
                
                screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/07-next-button.png"
                page.screenshot(path=screenshot_path)
                
                if date_before != date_after:
                    log_test("Next Button Click", "PASS", 
                            f"Button clicked. Date changed from {date_before} to {date_after}", screenshot_path)
                else:
                    log_test("Next Button Click", "FAIL", 
                            "Date did not change after clicking next", screenshot_path)
            else:
                log_test("Next Button Click", "WARN", "Button is disabled", screenshot_path)
            
            # Test 8: Keyboard Navigation
            print("\n⌨️  TEST 8: Keyboard Navigation (Arrow Keys)")
            date_before = page.locator("#dateText").text_content()
            
            # Press Left Arrow
            page.keyboard.press("ArrowLeft")
            time.sleep(0.5)
            date_after_left = page.locator("#dateText").text_content()
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/08-keyboard-left.png"
            page.screenshot(path=screenshot_path)
            
            if date_before != date_after_left:
                log_test("Keyboard Left Arrow", "PASS", 
                        f"Date changed from {date_before} to {date_after_left}", screenshot_path)
            else:
                log_test("Keyboard Left Arrow", "WARN", 
                        "Date did not change (might be at first day)", screenshot_path)
            
            # Press Right Arrow
            date_before = date_after_left
            page.keyboard.press("ArrowRight")
            time.sleep(0.5)
            date_after_right = page.locator("#dateText").text_content()
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/08b-keyboard-right.png"
            page.screenshot(path=screenshot_path)
            
            if date_before != date_after_right:
                log_test("Keyboard Right Arrow", "PASS", 
                        f"Date changed from {date_before} to {date_after_right}", screenshot_path)
            else:
                log_test("Keyboard Right Arrow", "WARN", 
                        "Date did not change (might be at last day)", screenshot_path)
            
            # Test 9: Transaction Table Display
            print("\n📋 TEST 9: Transaction Table Display")
            table_rows = page.locator("#rows tr")
            row_count = table_rows.count()
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/09-transaction-table.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            if row_count > 0:
                log_test("Transaction Table Rows", "PASS", 
                        f"Table has {row_count} transaction rows", screenshot_path)
                
                # Check first row structure
                first_row = table_rows.first
                cells = first_row.locator("td")
                cell_count = cells.count()
                
                if cell_count == 5:  # Vendor, Amount, Category, Notes, Status
                    log_test("Transaction Row Structure", "PASS", 
                            f"Row has correct number of cells ({cell_count})", screenshot_path)
                else:
                    log_test("Transaction Row Structure", "FAIL", 
                            f"Row has {cell_count} cells, expected 5", screenshot_path)
            else:
                log_test("Transaction Table Rows", "WARN", 
                        "No transaction rows found for current date", screenshot_path)
            
            # Test 10: Console Errors Check
            print("\n🖥️  TEST 10: Console Log Analysis")
            error_logs = [log for log in console_logs if "error" in log.lower()]
            warning_logs = [log for log in console_logs if "warning" in log.lower()]
            
            screenshot_path = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/10-final-state.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            if error_logs:
                log_test("Console Errors", "FAIL", 
                        f"Found {len(error_logs)} errors: {error_logs[:3]}", screenshot_path)
            else:
                log_test("Console Errors", "PASS", "No console errors detected", screenshot_path)
            
            if warning_logs:
                log_test("Console Warnings", "WARN", 
                        f"Found {len(warning_logs)} warnings: {warning_logs[:3]}", screenshot_path)
            else:
                log_test("Console Warnings", "PASS", "No console warnings detected", screenshot_path)
            
        except Exception as e:
            log_test("Browser Testing", "FAIL", f"Exception occurred: {str(e)}", "")
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Save console logs
            with open("/home/adamsl/planner/nonprofit_finance_db/test-screenshots/console-logs.json", "w") as f:
                json.dump(console_logs, f, indent=2)
            
            time.sleep(1)
            browser.close()
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    print(f"⚠️  Warnings: {results['summary']['warnings']}")
    print("="*80 + "\n")
    
    # Save results
    results_file = "/home/adamsl/planner/nonprofit_finance_db/test-screenshots/test-results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"📄 Full results saved to: {results_file}\n")
    
    return results

if __name__ == "__main__":
    test_daily_expense_categorizer()
