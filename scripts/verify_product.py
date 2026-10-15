#!/usr/bin/env python3
"""
End-to-End Product Verification Script

Tests the complete user flow:
1. Sign up
2. Run research (free tier)
3. Hit free tier limit
4. Upgrade to paid (test mode)
5. Re-run successfully

This script verifies the product is REALITY MODE ready.
"""

import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


import httpx

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "testpassword123"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_step(step: int, message: str):
    """Print a test step."""
    print(f"\n{Colors.BLUE}[STEP {step}]{Colors.RESET} {message}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ{Colors.RESET} {message}")


class ProductVerifier:
    """Product verification test suite."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.in_process = False
        try:
            httpx.get(f"{self.base_url}/health", timeout=1.5)
            self.client = httpx.Client(base_url=self.base_url, timeout=30.0)
            print_info(f"Connected to live Agent Factory service at {self.base_url}")
        except Exception:
            from fastapi.testclient import TestClient

            from agent_factory.api.main import app
            self.client = TestClient(app)
            self.in_process = True
            print_info(f"Live server at {self.base_url} not detected. Using direct FastAPI in-process test engine.")
        
        self.token: str | None = None
        self.user_id: str | None = None
        self.tenant_id: str | None = None

    def _url(self, path: str) -> str:
        if self.in_process:
            return path
        return f"{self.base_url}{path}"
    
    def step1_signup(self) -> bool:
        """Step 1: Sign up a new user."""
        print_step(1, "Signing up new user...")
        
        try:
            response = self.client.post(
                self._url("/api/v1/auth/signup"),
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code != 200:
                print_error(f"Signup failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            self.token = data.get("access_token")
            self.user_id = data.get("user_id")
            self.tenant_id = data.get("tenant_id")
            
            print_success(f"Signed up user: {TEST_EMAIL}")
            print_info(f"User ID: {self.user_id}")
            print_info(f"Tenant ID: {self.tenant_id}")
            return True
        except Exception as e:
            print_error(f"Signup exception: {e}")
            return False
    
    def step2_run_research_free(self) -> bool:
        """Step 2: Run research on free tier."""
        print_step(2, "Running research query (free tier)...")
        
        if not self.token:
            print_error("No authentication token")
            return False
        
        try:
            response = self.client.post(
                self._url("/api/v1/research"),
                json={
                    "query": "What are the latest developments in quantum computing?",
                    "max_results": 5,
                    "include_citations": True,
                    "depth": "quick"
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code != 200:
                print_error(f"Research failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            report_id = data.get("report_id")
            summary = data.get("summary", "")[:100]
            
            print_success(f"Research completed! Report ID: {report_id}")
            print_info(f"Summary preview: {summary}...")
            return True
        except Exception as e:
            print_error(f"Research exception: {e}")
            return False
    
    def step3_check_usage(self) -> bool:
        """Step 3: Check usage limits."""
        print_step(3, "Checking usage limits...")
        
        if not self.token:
            print_error("No authentication token")
            return False
        
        try:
            response = self.client.get(
                self._url("/api/v1/research/usage"),
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code != 200:
                print_error(f"Usage check failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            plan = data.get("plan_type")
            used = data.get("used", 0)
            limit = data.get("limit")
            remaining = data.get("remaining")
            
            print_success("Usage info retrieved")
            print_info(f"Plan: {plan}")
            print_info(f"Used: {used}/{limit}")
            print_info(f"Remaining: {remaining}")
            
            return True
        except Exception as e:
            print_error(f"Usage check exception: {e}")
            return False
    
    def step4_hit_limit(self) -> bool:
        """Step 4: Hit free tier limit by running multiple queries."""
        print_step(4, "Testing free tier limit enforcement...")
        
        if not self.token:
            print_error("No authentication token")
            return False
        
        # Run queries until we hit the limit
        for i in range(10):  # Try up to 10 times
            try:
                response = self.client.post(
                    self._url("/api/v1/research"),
                    json={
                        "query": f"Test query {i+1}",
                        "max_results": 5,
                        "depth": "quick"
                    },
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 429:
                    print_success(f"Limit hit after {i+1} queries (as expected)")
                    print_info(f"Response: {response.json()}")
                    return True
                elif response.status_code == 200:
                    print_info(f"Query {i+1} succeeded")
                else:
                    print_error(f"Unexpected status: {response.status_code}")
                    return False
            except Exception as e:
                print_error(f"Query exception: {e}")
                return False
        
        print_error("Did not hit limit after 10 queries")
        return False
    
    def step5_upgrade(self) -> bool:
        """Step 5: Upgrade to Pro plan (test mode)."""
        print_step(5, "Upgrading to Pro plan...")
        
        if not self.token:
            print_error("No authentication token")
            return False
        
        try:
            response = self.client.post(
                self._url("/api/v1/payments/upgrade"),
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code != 200:
                print_error(f"Upgrade failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            status = data.get("status")
            
            if status == "test_mode":
                print_success("Upgrade granted (test mode - Stripe not configured)")
                print_info("In production, this would redirect to Stripe checkout")
                return True
            elif status == "checkout_created":
                print_success("Stripe checkout session created")
                print_info(f"Checkout URL: {data.get('checkout_url')}")
                return True
            elif status == "already_upgraded":
                print_success("Already on paid plan")
                return True
            else:
                print_error(f"Unexpected upgrade status: {status}")
                return False
        except Exception as e:
            print_error(f"Upgrade exception: {e}")
            return False
    
    def step6_rerun_after_upgrade(self) -> bool:
        """Step 6: Re-run research after upgrade."""
        print_step(6, "Running research after upgrade...")
        
        if not self.token:
            print_error("No authentication token")
            return False
        
        try:
            response = self.client.post(
                self._url("/api/v1/research"),
                json={
                    "query": "What are the benefits of renewable energy?",
                    "max_results": 10,  # Pro tier allows more results
                    "depth": "standard"  # Pro tier allows standard depth
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code != 200:
                print_error(f"Research failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            report_id = data.get("report_id")
            
            print_success(f"Research completed after upgrade! Report ID: {report_id}")
            return True
        except Exception as e:
            print_error(f"Research exception: {e}")
            return False
    
    def step7_list_reports(self) -> bool:
        """Step 7: List past reports."""
        print_step(7, "Listing past research reports...")
        
        if not self.token:
            print_error("No authentication token")
            return False
        
        try:
            response = self.client.get(
                self._url("/api/v1/research/reports"),
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code != 200:
                print_error(f"List reports failed: {response.status_code} - {response.text}")
                return False
            
            data = response.json()
            count = len(data)
            
            print_success(f"Retrieved {count} past reports")
            return True
        except Exception as e:
            print_error(f"List reports exception: {e}")
            return False
    
    def run_all(self) -> bool:
        """Run all verification steps."""
        print(f"\n{Colors.BLUE}{'='*60}")
        print("PRODUCT VERIFICATION - REALITY MODE")
        print(f"{'='*60}{Colors.RESET}\n")
        print(f"Base URL: {self.base_url}")
        print(f"Test Email: {TEST_EMAIL}\n")
        
        steps = [
            ("Signup", self.step1_signup),
            ("Run Research (Free)", self.step2_run_research_free),
            ("Check Usage", self.step3_check_usage),
            ("Hit Limit", self.step4_hit_limit),
            ("Upgrade", self.step5_upgrade),
            ("Re-run After Upgrade", self.step6_rerun_after_upgrade),
            ("List Reports", self.step7_list_reports),
        ]
        
        results = []
        for name, step_func in steps:
            try:
                result = step_func()
                results.append((name, result))
                if not result:
                    print_error(f"Step '{name}' failed. Stopping verification.")
                    break
                time.sleep(1)  # Small delay between steps
            except Exception as e:
                print_error(f"Step '{name}' raised exception: {e}")
                results.append((name, False))
                break
        
        # Summary
        print(f"\n{Colors.BLUE}{'='*60}")
        print("VERIFICATION SUMMARY")
        print(f"{'='*60}{Colors.RESET}\n")
        
        all_passed = True
        for name, result in results:
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"{status} - {name}")
            if not result:
                all_passed = False
        
        print()
        if all_passed:
            print_success("ALL STEPS PASSED - PRODUCT IS REALITY MODE READY!")
            return True
        else:
            print_error("SOME STEPS FAILED - PRODUCT NEEDS FIXES")
            return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify product end-to-end")
    parser.add_argument("--url", default=BASE_URL, help="API base URL")
    args = parser.parse_args()
    
    verifier = ProductVerifier(args.url)
    success = verifier.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
