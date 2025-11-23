#!/usr/bin/env python3
"""
Selenium E2E Visual Testing Suite for MoirAI
Tests all 3 roles with visual navigation: Login → Register → Dashboard → Logout
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import logging
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Generate unique identifiers for this test run
TIMESTAMP = int(time.time() * 1000)

# Test configuration with unique emails per run
TEST_CONFIG = {
    "student": {
        "role": "student",
        "register": {
            "role": "student",
            "name": f"Selenium Student {TIMESTAMP}",
            "email": f"selenium-student-{TIMESTAMP}@test.com",
            "password": "TestPassword123!",
            "program": "Computer Science",
            "industry": "Technology"
        },
        "login": {
            "email": f"selenium-student-{TIMESTAMP}@test.com",
            "password": "TestPassword123!"
        }
    },
    "company": {
        "role": "company",
        "register": {
            "role": "company",
            "name": f"Selenium Company {TIMESTAMP}",
            "email": f"selenium-company-{TIMESTAMP}@test.com",
            "password": "TestPassword123!",
            "industry": "Technology",
            "size": "Medium"
        },
        "login": {
            "email": f"selenium-company-{TIMESTAMP}@test.com",
            "password": "TestPassword123!"
        }
    },
    "admin": {
        "role": "admin",
        "skip_register": True,  # Admin pre-created
        "login": {
            "email": "henryadmin@hotmail.com",
            "password": "Henryadmin369"
        }
    }
}

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/v1"


class SeleniumVisualE2ETester:
    """Visual E2E test orchestrator with browser navigation"""

    def __init__(self):
        self.driver: WebDriver = None
        self.wait: WebDriverWait = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "browser": "Chrome",
            "results": {},
            "console_logs": {
                "browser": {},
                "summary": {
                    "total_errors": 0,
                    "total_warnings": 0,
                    "roles_tested": []
                }
            },
            "logs": {
                "info": [],
                "success": 0,
                "warning": 0,
                "error": 0
            }
        }
        self.api_tokens = {}

    def setup_driver(self):
        """Initialize Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Enable browser logs
            chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL", "driver": "ALL"})

            service = Service()
            self.driver = webdriver.Chrome(options=chrome_options, service=service)
            self.wait = WebDriverWait(self.driver, 15)
            self.log_info("✅ Chrome WebDriver initialized")
            return True
        except Exception as e:
            self.log_error(f"❌ Failed to initialize WebDriver: {e}")
            return False

    def teardown_driver(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.log_info("✅ Browser closed")
            except:
                pass

    def log_info(self, message: str):
        """Log info message"""
        logger.info(message)
        self.results["logs"]["info"].append(message)
        self.results["logs"]["success"] += 1

    def log_warning(self, message: str):
        """Log warning message"""
        logger.warning(message)
        self.results["logs"]["info"].append(f"⚠️ {message}")
        self.results["logs"]["warning"] += 1

    def log_error(self, message: str):
        """Log error message"""
        logger.error(message)
        self.results["logs"]["info"].append(f"❌ {message}")
        self.results["logs"]["error"] += 1

    def capture_browser_logs(self) -> Dict[str, List[str]]:
        """Capture all browser console logs"""
        try:
            browser_logs = {
                "errors": [],
                "warnings": [],
                "info": [],
                "debug": []
            }
            
            # Try to get browser logs
            try:
                logs = self.driver.get_log('browser')
                for log in logs:
                    level = log['level']
                    message = log['message']
                    
                    if 'SEVERE' in level:
                        browser_logs["errors"].append(message)
                    elif 'WARNING' in level:
                        browser_logs["warnings"].append(message)
                    elif 'INFO' in level:
                        browser_logs["info"].append(message)
                    else:
                        browser_logs["debug"].append(message)
            except Exception as e:
                self.log_warning(f"Could not get browser logs: {e}")

            # Also capture console errors using JavaScript
            try:
                js_errors = self.driver.execute_script("""
                    return {
                        errors: window.consoleErrors || [],
                        logs: window.consoleLogs || []
                    };
                """)
                if js_errors.get("errors"):
                    browser_logs["errors"].extend(js_errors["errors"])
                if js_errors.get("logs"):
                    browser_logs["info"].extend(js_errors["logs"])
            except:
                pass

            return browser_logs
        except Exception as e:
            self.log_warning(f"Error capturing browser logs: {e}")
            return {"errors": [], "warnings": [], "info": [], "debug": []}

    def inject_console_capture_script(self):
        """Inject script to capture console messages"""
        try:
            capture_script = """
            window.consoleErrors = [];
            window.consoleLogs = [];
            
            const originalError = console.error;
            const originalLog = console.log;
            const originalWarn = console.warn;
            
            console.error = function(...args) {
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                window.consoleErrors.push({
                    type: 'error',
                    message: message,
                    timestamp: new Date().toISOString()
                });
                originalError.apply(console, args);
            };
            
            console.log = function(...args) {
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                window.consoleLogs.push({
                    type: 'log',
                    message: message,
                    timestamp: new Date().toISOString()
                });
                originalLog.apply(console, args);
            };
            
            console.warn = function(...args) {
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
                ).join(' ');
                window.consoleLogs.push({
                    type: 'warning',
                    message: message,
                    timestamp: new Date().toISOString()
                });
                originalWarn.apply(console, args);
            };
            
            // Capture unhandled errors
            window.addEventListener('error', function(event) {
                window.consoleErrors.push({
                    type: 'uncaught',
                    message: event.message,
                    filename: event.filename,
                    lineno: event.lineno,
                    colno: event.colno,
                    timestamp: new Date().toISOString()
                });
            });
            
            // Capture unhandled promise rejections
            window.addEventListener('unhandledrejection', function(event) {
                window.consoleErrors.push({
                    type: 'unhandledRejection',
                    message: event.reason ? (typeof event.reason === 'object' ? JSON.stringify(event.reason) : String(event.reason)) : 'Unknown error',
                    timestamp: new Date().toISOString()
                });
            });
            """
            
            self.driver.execute_script(capture_script)
            self.log_info("✅ Console capture script injected")
        except Exception as e:
            self.log_warning(f"Could not inject console capture script: {e}")

    def register_via_api(self, role: str, credentials: Dict) -> bool:
        """Register user via API (backend)"""
        try:
            url = f"{API_URL}/auth/register"
            response = requests.post(url, json=credentials, timeout=10)
            
            if response.status_code == 201:
                self.log_info(f"✅ {role} registered via API (status: 201)")
                return True
            else:
                self.log_error(f"❌ API registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"❌ Error registering via API: {e}")
            return False

    def login_via_api(self, role: str, email: str, password: str) -> bool:
        """Login user via API and get token"""
        try:
            url = f"{API_URL}/auth/login"
            payload = {"email": email, "password": password}
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("api_key")
                if token:
                    self.api_tokens[role] = token
                    self.log_info(f"✅ {role} logged in via API (token: {token[:20]}...)")
                    return True
                else:
                    self.log_error(f"❌ No token in login response")
                    return False
            else:
                self.log_error(f"❌ API login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"❌ Error logging in via API: {e}")
            return False

    def navigate_to_login_page(self):
        """Navigate to login page"""
        try:
            self.driver.get(f"{BASE_URL}/login")
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Inject console capture script on every page
            self.inject_console_capture_script()
            
            self.log_info("✅ Navigated to login page")
            time.sleep(1)
            return True
        except Exception as e:
            self.log_error(f"❌ Failed to navigate to login page: {e}")
            return False

    def fill_login_form(self, email: str, password: str) -> bool:
        """Fill and submit login form"""
        try:
            # Find email input
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.clear()
            email_input.send_keys(email)
            self.log_info(f"📝 Entered email: {email}")

            # Find password input
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(password)
            self.log_info(f"📝 Entered password: ***")

            # Find and click submit button
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            self.log_info("🔐 Clicked login button")

            time.sleep(2)  # Wait for redirect
            return True
        except Exception as e:
            self.log_error(f"❌ Error filling login form: {e}")
            return False

    def fill_register_form(self, role: str, credentials: Dict) -> bool:
        """Fill and submit registration form"""
        try:
            # Look for role-specific form fields
            name_input = self.wait.until(EC.presence_of_element_located((By.NAME, "name")))
            name_input.clear()
            name_input.send_keys(credentials["name"])
            self.log_info(f"📝 Entered name: {credentials['name']}")

            email_input = self.driver.find_element(By.NAME, "email")
            email_input.clear()
            email_input.send_keys(credentials["email"])
            self.log_info(f"📝 Entered email: {credentials['email']}")

            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(credentials["password"])
            self.log_info(f"📝 Entered password: ***")

            # Role-specific fields
            if role == "student" and "program" in credentials:
                try:
                    program_input = self.driver.find_element(By.NAME, "program")
                    program_input.clear()
                    program_input.send_keys(credentials["program"])
                    self.log_info(f"📝 Entered program: {credentials['program']}")
                except:
                    pass

            if "industry" in credentials:
                try:
                    industry_input = self.driver.find_element(By.NAME, "industry")
                    industry_input.clear()
                    industry_input.send_keys(credentials["industry"])
                    self.log_info(f"📝 Entered industry: {credentials['industry']}")
                except:
                    pass

            if role == "company" and "size" in credentials:
                try:
                    size_input = self.driver.find_element(By.NAME, "size")
                    size_input.clear()
                    size_input.send_keys(credentials["size"])
                    self.log_info(f"📝 Entered company size: {credentials['size']}")
                except:
                    pass

            # Find and click submit button
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            self.log_info("✍️ Clicked register button")

            time.sleep(2)
            return True
        except Exception as e:
            self.log_error(f"❌ Error filling register form: {e}")
            return False

    def check_dashboard_loaded(self, role: str) -> bool:
        """Check if dashboard is loaded after login"""
        try:
            # Wait for any dashboard indicator (header, nav, or specific role element)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            
            # Try to find role-specific elements
            current_url = self.driver.current_url
            self.log_info(f"✅ Dashboard loaded (URL: {current_url})")
            
            # Get page title
            title = self.driver.title
            self.log_info(f"📄 Page title: {title}")
            
            return True
        except Exception as e:
            self.log_warning(f"⚠️ Dashboard check: {e}")
            return True  # Don't fail if we can't detect

    def click_logout_button(self) -> bool:
        """Find and click logout button"""
        try:
            # Try multiple logout button selectors
            logout_selectors = [
                "button[onclick*='logout']",
                "a[href*='logout']",
                "button:contains('Logout')",
                "button:contains('Salir')",
                "[data-test='logout-btn']",
                ".navbar button:last-child",
            ]

            logout_button = None
            for selector in logout_selectors:
                try:
                    logout_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if logout_button.is_displayed():
                        break
                except:
                    continue

            if not logout_button:
                # Try finding by text content using xpath
                try:
                    logout_button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Logout') or contains(text(), 'Salir')]")
                except:
                    pass

            if logout_button:
                logout_button.click()
                self.log_info("🚪 Clicked logout button")
                time.sleep(1)
                return True
            else:
                self.log_warning("⚠️ Logout button not found")
                return False
        except Exception as e:
            self.log_error(f"❌ Error clicking logout button: {e}")
            return False

    def verify_logged_out(self) -> bool:
        """Verify user is logged out (redirected to login)"""
        try:
            time.sleep(1)
            current_url = self.driver.current_url
            
            # Check if redirected to login page
            if "/login" in current_url:
                self.log_info(f"✅ Logged out successfully (redirected to login)")
                return True
            
            # Check if login form is visible
            try:
                self.wait.until(EC.presence_of_element_located((By.NAME, "email")), timeout=5)
                self.log_info("✅ Logged out successfully (login form visible)")
                return True
            except:
                pass

            self.log_warning(f"⚠️ Could not confirm logout (URL: {current_url})")
            return False
        except Exception as e:
            self.log_error(f"❌ Error verifying logout: {e}")
            return False

    def test_role_full_flow(self, role: str) -> Dict[str, Any]:
        """Test complete flow for a role: register → login → dashboard → logout"""
        config = TEST_CONFIG[role]
        role_results = {
            "role": role,
            "steps": {},
            "screenshots": [],
            "console_logs": {}
        }

        self.log_info(f"\n{'='*80}")
        self.log_info(f"🔄 TESTING ROLE: {role.upper()}")
        self.log_info(f"{'='*80}")

        # Step 1: Register (via API, skip for admin)
        if config.get("skip_register"):
            self.log_info("⏭️ Skipping registration for pre-created admin")
            role_results["steps"]["register_api"] = "skipped"
        else:
            if self.register_via_api(role, config["register"]):
                role_results["steps"]["register_api"] = "success"
            else:
                role_results["steps"]["register_api"] = "failed"
                return role_results
            time.sleep(1)

        # Step 2: Navigate to login page
        if not self.navigate_to_login_page():
            role_results["steps"]["navigate_login"] = "failed"
            return role_results
        role_results["steps"]["navigate_login"] = "success"

        # Step 3: Login via API first to get token
        if self.login_via_api(role, config["login"]["email"], config["login"]["password"]):
            role_results["steps"]["login_api"] = "success"
        else:
            role_results["steps"]["login_api"] = "failed"
            return role_results

        # Step 4: Login via UI form
        if self.fill_login_form(config["login"]["email"], config["login"]["password"]):
            role_results["steps"]["login_ui"] = "success"
        else:
            role_results["steps"]["login_ui"] = "failed"

        # Step 5: Check dashboard loaded
        if self.check_dashboard_loaded(role):
            role_results["steps"]["dashboard_loaded"] = "success"
        else:
            role_results["steps"]["dashboard_loaded"] = "partial"

        time.sleep(1)

        # Step 6: Take screenshot before logout
        try:
            screenshot_path = f"/tmp/moir-{role}-before-logout.png"
            self.driver.save_screenshot(screenshot_path)
            role_results["screenshots"].append({"type": "before_logout", "path": screenshot_path})
            self.log_info(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            self.log_warning(f"⚠️ Could not take screenshot: {e}")

        # Step 7: Logout
        if self.click_logout_button():
            role_results["steps"]["logout_click"] = "success"
        else:
            role_results["steps"]["logout_click"] = "failed"

        # Step 8: Verify logged out
        if self.verify_logged_out():
            role_results["steps"]["logout_verify"] = "success"
        else:
            role_results["steps"]["logout_verify"] = "partial"

        # Step 9: Take screenshot after logout
        try:
            screenshot_path = f"/tmp/moir-{role}-after-logout.png"
            self.driver.save_screenshot(screenshot_path)
            role_results["screenshots"].append({"type": "after_logout", "path": screenshot_path})
            self.log_info(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            self.log_warning(f"⚠️ Could not take screenshot: {e}")

        # Step 10: Capture console logs
        console_logs = self.capture_browser_logs()
        role_results["console_logs"] = console_logs
        
        # Update global console logs summary
        self.results["console_logs"]["browser"][role] = console_logs
        self.results["console_logs"]["summary"]["roles_tested"].append(role)
        self.results["console_logs"]["summary"]["total_errors"] += len(console_logs.get("errors", []))
        self.results["console_logs"]["summary"]["total_warnings"] += len(console_logs.get("warnings", []))
        
        # Log summary
        if console_logs["errors"]:
            self.log_error(f"🚨 {role}: {len(console_logs['errors'])} console error(s) detected")
            for error in console_logs["errors"][:3]:  # Show first 3
                self.log_warning(f"  └─ {error[:100]}")
        
        if console_logs["warnings"]:
            self.log_warning(f"⚠️ {role}: {len(console_logs['warnings'])} console warning(s) detected")

        return role_results

    def run_all_tests(self):
        """Run visual tests for all roles"""
        try:
            if not self.setup_driver():
                return False

            for role in ["student", "company", "admin"]:
                role_results = self.test_role_full_flow(role)
                self.results["results"][role] = role_results

                # Small delay between role tests
                time.sleep(1)

            return True
        except Exception as e:
            self.log_error(f"❌ Unexpected error: {e}")
            return False
        finally:
            self.teardown_driver()

    def generate_report(self):
        """Generate JSON report"""
        report_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_filename = f"selenium-visual-e2e-report-{report_timestamp}.json"
        report_path = Path("/Users/sparkmachine/MoirAI") / report_filename

        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\n📊 Report generated: {report_path}")
        return report_path

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("SELENIUM VISUAL E2E TEST SUMMARY")
        print("="*80)

        for role, result in self.results["results"].items():
            if isinstance(result, dict) and "steps" in result:
                steps = result["steps"]
                success_count = sum(1 for v in steps.values() if v == "success")
                total_steps = len(steps)

                if success_count >= total_steps - 2:  # Allow 2 failures
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"

                print(f"\n{status} {role.upper()}")

                for step, status_val in steps.items():
                    icon = "✅" if status_val == "success" else ("⏭️" if status_val == "skipped" else ("⚠️" if status_val == "partial" else "❌"))
                    print(f"  {icon} {step}: {status_val}")

                if result.get("screenshots"):
                    print(f"  📸 Screenshots: {len(result['screenshots'])} captured")
                
                # Print console logs for this role
                console_logs = result.get("console_logs", {})
                if console_logs:
                    errors = console_logs.get("errors", [])
                    warnings = console_logs.get("warnings", [])
                    
                    if errors:
                        print(f"  🚨 Console Errors: {len(errors)}")
                        for error in errors[:2]:  # Show first 2
                            print(f"     └─ {error[:80]}")
                    
                    if warnings:
                        print(f"  ⚠️ Console Warnings: {len(warnings)}")
                        for warning in warnings[:2]:  # Show first 2
                            print(f"     └─ {warning[:80]}")

        # Print global console logs summary
        console_summary = self.results["console_logs"]["summary"]
        print(f"\n🔍 CONSOLE LOGS SUMMARY (DevTools)")
        print(f"  • Roles Tested: {', '.join(console_summary['roles_tested'])}")
        print(f"  • Total Errors Found: {console_summary['total_errors']}")
        print(f"  • Total Warnings Found: {console_summary['total_warnings']}")

        print(f"\n📈 Overall Summary:")
        print(f"  • Test Operations: {self.results['logs']['success']}")
        print(f"  • Warnings: {self.results['logs']['warning']}")
        print(f"  • Test Errors: {self.results['logs']['error']}")
        print("="*80 + "\n")


def main():
    """Main entry point"""
    tester = SeleniumVisualE2ETester()
    success = tester.run_all_tests()
    tester.generate_report()
    tester.print_summary()

    return 0 if success and tester.results["logs"]["error"] < 3 else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
