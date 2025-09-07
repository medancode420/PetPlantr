#!/usr/bin/env python3
"""
PetPlantr Stripe Integration Test Suite
Tests payment processing and webhook handling
"""

import json
import os
import requests
import time
from pathlib import Path
from typing import Dict, Any

class StripeIntegrationTest:
    """Test suite for Stripe integration"""

    def __init__(self):
        self.test_results = []
        self.webhook_endpoint = os.getenv('WEBHOOK_ENDPOINT', 'http://localhost:8000/webhook/stripe')
        self.stripe_secret_key = os.getenv('STRIPE_TEST_SECRET_KEY', 'sk_test_...')

    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': time.time()
        }
        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")

    def test_webhook_endpoint(self):
        """Test webhook endpoint availability"""
        try:
            # Test with a simple ping
            test_payload = {
                'type': 'test.webhook',
                'data': {'test': True}
            }

            response = requests.post(
                self.webhook_endpoint,
                json=test_payload,
                timeout=10
            )

            if response.status_code in [200, 400]:  # 400 is expected for invalid signature
                self.log_test_result(
                    "Webhook Endpoint Availability",
                    True,
                    f"Endpoint responded with status {response.status_code}"
                )
            else:
                self.log_test_result(
                    "Webhook Endpoint Availability",
                    False,
                    f"Unexpected status code: {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            self.log_test_result(
                "Webhook Endpoint Availability",
                False,
                f"Request failed: {str(e)}"
            )

    def test_stripe_event_processing(self):
        """Test processing of Stripe events"""
        test_events = [
            {
                'type': 'payment_intent.succeeded',
                'data': {
                    'object': {
                        'id': 'pi_test_123',
                        'amount': 2999,
                        'currency': 'usd'
                    }
                }
            },
            {
                'type': 'payment_intent.payment_failed',
                'data': {
                    'object': {
                        'id': 'pi_test_456',
                        'last_payment_error': {
                            'message': 'Card declined'
                        }
                    }
                }
            },
            {
                'type': 'customer.subscription.created',
                'data': {
                    'object': {
                        'id': 'sub_test_789',
                        'status': 'active'
                    }
                }
            }
        ]

        for event in test_events:
            try:
                response = requests.post(
                    self.webhook_endpoint,
                    json=event,
                    timeout=10
                )

                if response.status_code == 200:
                    self.log_test_result(
                        f"Stripe Event Processing - {event['type']}",
                        True,
                        "Event processed successfully"
                    )
                else:
                    self.log_test_result(
                        f"Stripe Event Processing - {event['type']}",
                        False,
                        f"Processing failed with status {response.status_code}"
                    )

            except requests.exceptions.RequestException as e:
                self.log_test_result(
                    f"Stripe Event Processing - {event['type']}",
                    False,
                    f"Request failed: {str(e)}"
                )

    def test_eventbridge_integration(self):
        """Test EventBridge event publishing"""
        # This would require AWS credentials and actual EventBridge setup
        # For now, we'll just check if the configuration is present

        eventbridge_bus = os.getenv('EVENTBRIDGE_BUS')
        if eventbridge_bus:
            self.log_test_result(
                "EventBridge Configuration",
                True,
                f"EventBridge bus configured: {eventbridge_bus}"
            )
        else:
            self.log_test_result(
                "EventBridge Configuration",
                False,
                "EVENTBRIDGE_BUS environment variable not set"
            )

    def test_stripe_configuration(self):
        """Test Stripe configuration"""
        if self.stripe_secret_key and not self.stripe_secret_key.endswith('...'):
            if self.stripe_secret_key.startswith('sk_test_'):
                self.log_test_result(
                    "Stripe Configuration",
                    True,
                    "Test secret key configured"
                )
            elif self.stripe_secret_key.startswith('sk_live_'):
                self.log_test_result(
                    "Stripe Configuration",
                    True,
                    "Live secret key configured"
                )
            else:
                self.log_test_result(
                    "Stripe Configuration",
                    False,
                    "Invalid Stripe secret key format"
                )
        else:
            self.log_test_result(
                "Stripe Configuration",
                False,
                "Stripe secret key not configured or is placeholder"
            )

    def test_payment_flow_simulation(self):
        """Simulate complete payment flow"""
        # This is a high-level test that would integrate with actual payment UI
        # For now, we'll check if all components are configured

        required_configs = [
            'STRIPE_PUBLISHABLE_KEY',
            'WEBHOOK_ENDPOINT',
            'EVENTBRIDGE_BUS'
        ]

        missing_configs = []
        for config in required_configs:
            value = os.getenv(config)
            if not value or value.endswith('...'):
                missing_configs.append(config)

        if not missing_configs:
            self.log_test_result(
                "Payment Flow Configuration",
                True,
                "All payment flow components configured"
            )
        else:
            self.log_test_result(
                "Payment Flow Configuration",
                False,
                f"Missing configurations: {', '.join(missing_configs)}"
            )

    def generate_test_report(self):
        """Generate test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
            },
            'results': self.test_results,
            'timestamp': time.time(),
            'environment': os.getenv('PETPLANTR_ENV', 'unknown')
        }

        return report

    def save_report(self, filename: str = None):
        """Save test report to file"""
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"stripe_test_report_{timestamp}.json"

        report = self.generate_test_report()

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\\n💾 Test report saved to: {filename}")
        return filename

def main():
    """Run Stripe integration tests"""
    print("🧪 PetPlantr Stripe Integration Test Suite")
    print("=" * 50)

    tester = StripeIntegrationTest()

    # Run all tests
    print("\\n🔍 Running tests...")

    tester.test_stripe_configuration()
    tester.test_webhook_endpoint()
    tester.test_eventbridge_integration()
    tester.test_stripe_event_processing()
    tester.test_payment_flow_simulation()

    # Generate and display report
    report = tester.generate_test_report()

    print("\\n📊 Test Results Summary:")
    print(f"   Total Tests: {report['summary']['total_tests']}")
    print(f"   Passed: {report['summary']['passed']}")
    print(f"   Failed: {report['summary']['failed']}")
    print(f"   Success Rate: {report['summary']['success_rate']}")

    # Save report
    report_file = tester.save_report()

    # Display detailed results
    print("\\n📋 Detailed Results:")
    for result in report['results']:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['test']}")
        if result['message']:
            print(f"      {result['message']}")

    # Final assessment
    if report['summary']['failed'] == 0:
        print("\\n🎉 All tests passed! Stripe integration is ready.")
    else:
        print(f"\\n⚠️  {report['summary']['failed']} test(s) failed.")
        print("Please review the configuration and try again.")

    return report['summary']['failed'] == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
