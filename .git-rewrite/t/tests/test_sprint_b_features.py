#!/usr/bin/env python3
"""
Sprint B Feature Tests - Hedging and Mesh Governor
Comprehensive testing for latency optimization features
"""
import asyncio
import time
import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRequestHedging(unittest.TestCase):
    """Test request hedging functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_settings = Mock()
        self.mock_settings.feature_hedging = True
        self.mock_settings.hedging_delay_ms = 100
        self.mock_settings.hedging_max_extra = 1
        self.mock_settings.hedging_cost_limit_per_hour = 10.0
        
    async def test_hedging_disabled_single_request(self):
        """Test that hedging disabled results in single request."""
        from src.services.hedging import HedgedRequest
        
        # Mock disabled hedging
        with patch('src.services.hedging.settings') as mock_settings:
            mock_settings.feature_hedging = False
            
            async def mock_request():
                await asyncio.sleep(0.05)  # 50ms
                return "result"
            
            hedger = HedgedRequest("test")
            start_time = time.time()
            result = await hedger.race(mock_request, timeout_sec=1.0)
            duration = time.time() - start_time
            
            self.assertEqual(result, "result")
            self.assertIsNone(hedger.secondary_task)
            self.assertLess(duration, 0.1)  # Should complete quickly
    
    async def test_hedging_primary_wins_fast(self):
        """Test that fast primary request wins without starting secondary."""
        from src.services.hedging import HedgedRequest
        
        with patch('src.services.hedging.settings') as mock_settings:
            mock_settings.feature_hedging = True
            mock_settings.hedging_delay_ms = 200  # 200ms delay
            
            with patch('src.services.hedging.cost_tracker') as mock_tracker:
                mock_tracker.should_allow_hedging.return_value = True
                
                async def fast_request():
                    await asyncio.sleep(0.05)  # 50ms - faster than delay
                    return "fast_result"
                
                hedger = HedgedRequest("test")
                result = await hedger.race(fast_request, timeout_sec=1.0)
                
                self.assertEqual(result, "fast_result")
                self.assertIsNone(hedger.secondary_task)
    
    async def test_hedging_secondary_wins_race(self):
        """Test that secondary request can win the race."""
        from src.services.hedging import HedgedRequest
        
        with patch('src.services.hedging.settings') as mock_settings:
            mock_settings.feature_hedging = True
            mock_settings.hedging_delay_ms = 50  # Short delay
            
            with patch('src.services.hedging.cost_tracker') as mock_tracker:
                mock_tracker.should_allow_hedging.return_value = True
                mock_tracker.record_hedged_request.return_value = 1.0
                
                call_count = 0
                async def variable_request():
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        # Primary is slow
                        await asyncio.sleep(0.3)
                        return "slow_primary"
                    else:
                        # Secondary is fast  
                        await asyncio.sleep(0.1)
                        return "fast_secondary"
                
                hedger = HedgedRequest("test")
                result = await hedger.race(variable_request, timeout_sec=1.0)
                
                # Secondary should win
                self.assertEqual(result, "fast_secondary")
                self.assertEqual(call_count, 2)  # Both requests started
    
    def test_cost_tracking(self):
        """Test hedging cost tracking and budget enforcement."""
        from src.services.hedging import CostTracker
        
        tracker = CostTracker()
        tracker.breed_cost_estimate = 0.01  # $0.01 per request
        
        # Record some requests
        for _ in range(5):
            cost = tracker.record_hedged_request("breed")
        
        # Should accumulate cost
        current_cost = tracker.get_current_hourly_cost()
        self.assertEqual(current_cost, 0.05)
        
        # Should allow hedging under budget
        tracker.hedging_disabled_until = 0
        with patch.object(tracker, 'get_current_hourly_cost', return_value=5.0):
            self.assertTrue(tracker.should_allow_hedging())
        
        # Should block hedging over budget
        with patch.object(tracker, 'get_current_hourly_cost', return_value=15.0):
            with patch('src.services.hedging.settings') as mock_settings:
                mock_settings.hedging_cost_limit_per_hour = 10.0
                self.assertFalse(tracker.should_allow_hedging())

class TestMeshGovernor(unittest.TestCase):
    """Test mesh fidelity governor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_settings = Mock()
        self.mock_settings.feature_mesh_governor = True
        self.mock_settings.governor_qdepth_warn = 80
        self.mock_settings.governor_qdepth_drop = 120
        self.mock_settings.governor_tokens_warn = 5
        self.mock_settings.governor_tokens_drop = 8
    
    def test_baseline_preset_normal_load(self):
        """Test baseline preset selection under normal load."""
        from src.services.mesh_governor import select_mesh_preset
        
        with patch('src.services.mesh_governor.settings') as mock_settings:
            mock_settings.feature_mesh_governor = True
            mock_settings.governor_qdepth_warn = 80
            mock_settings.governor_tokens_warn = 5
            
            preset = select_mesh_preset(queue_depth=10, tokens_in_use=2)
            
            self.assertEqual(preset["preset"], "baseline")
            self.assertEqual(preset["engine"], "shape-e")
            self.assertEqual(preset["steps"], 64)
            self.assertFalse(preset["governor_applied"])
    
    def test_warn_preset_medium_load(self):
        """Test warn preset selection under medium load."""
        from src.services.mesh_governor import select_mesh_preset
        
        with patch('src.services.mesh_governor.settings') as mock_settings:
            mock_settings.feature_mesh_governor = True
            mock_settings.governor_qdepth_warn = 80
            mock_settings.governor_qdepth_drop = 120
            mock_settings.governor_tokens_warn = 5
            mock_settings.governor_tokens_drop = 8
            
            # Queue depth triggers warning
            preset = select_mesh_preset(queue_depth=90, tokens_in_use=3)
            
            self.assertEqual(preset["preset"], "warn")
            self.assertEqual(preset["engine"], "shape-e")
            self.assertEqual(preset["steps"], 40)
            self.assertTrue(preset["governor_applied"])
            self.assertIn("queue_warning", preset["reason"])
    
    def test_drop_preset_high_load(self):
        """Test drop preset selection under high load."""
        from src.services.mesh_governor import select_mesh_preset
        
        with patch('src.services.mesh_governor.settings') as mock_settings:
            mock_settings.feature_mesh_governor = True
            mock_settings.governor_qdepth_drop = 120
            mock_settings.governor_tokens_drop = 8
            
            # Both queue and tokens trigger drop
            preset = select_mesh_preset(queue_depth=150, tokens_in_use=10)
            
            self.assertEqual(preset["preset"], "drop")
            self.assertEqual(preset["engine"], "point-e")
            self.assertEqual(preset["steps"], 32)
            self.assertTrue(preset["governor_applied"])
            self.assertIn("critical", preset["reason"])
    
    def test_governor_disabled(self):
        """Test behavior when governor is disabled."""
        from src.services.mesh_governor import select_mesh_preset
        
        with patch('src.services.mesh_governor.settings') as mock_settings:
            mock_settings.feature_mesh_governor = False
            
            # Even under high load, should return baseline
            preset = select_mesh_preset(queue_depth=200, tokens_in_use=15)
            
            self.assertEqual(preset["preset"], "baseline")
            self.assertFalse(preset["governor_applied"])
            self.assertEqual(preset["reason"], "governor_disabled")
    
    def test_governor_transitions(self):
        """Test governor transition tracking."""
        from src.services.mesh_governor import mesh_governor
        
        with patch('src.services.mesh_governor.settings') as mock_settings:
            mock_settings.feature_mesh_governor = True
            mock_settings.governor_qdepth_warn = 80
            mock_settings.governor_qdepth_drop = 120
            mock_settings.governor_tokens_warn = 5
            mock_settings.governor_tokens_drop = 8
            
            # Start with baseline
            mesh_governor.current_preset = mesh_governor.presets[mesh_governor.current_preset.__class__.BASELINE]
            
            # Trigger transition to warn
            preset1 = mesh_governor.select_preset(queue_depth=90, tokens_in_use=3)
            self.assertEqual(preset1["preset"], "warn")
            
            # Trigger transition to drop
            preset2 = mesh_governor.select_preset(queue_depth=150, tokens_in_use=10)
            self.assertEqual(preset2["preset"], "drop")
            
            # Check transition history
            stats = mesh_governor.get_stats()
            self.assertGreater(stats["transitions_count"], 0)

class TestSprintBIntegration(unittest.TestCase):
    """Integration tests for Sprint B features."""
    
    async def test_hedged_breed_detection_flow(self):
        """Test complete hedged breed detection workflow."""
        # Mock the complete breed detection flow with hedging
        
        async def mock_replicate_call():
            await asyncio.sleep(0.1)
            return {"breed": "golden_retriever", "confidence": 0.95}
        
        # Test with hedging enabled
        from src.services.hedging import hedged_request
        
        with patch('src.services.hedging.settings') as mock_settings:
            mock_settings.feature_hedging = True
            mock_settings.hedging_delay_ms = 50
            
            with patch('src.services.hedging.cost_tracker') as mock_tracker:
                mock_tracker.should_allow_hedging.return_value = True
                mock_tracker.record_hedged_request.return_value = 1.0
                
                async with hedged_request("breed_detection") as hedger:
                    result = await hedger.race(mock_replicate_call, timeout_sec=2.0)
                
                self.assertEqual(result["breed"], "golden_retriever")
    
    def test_mesh_generation_with_governor(self):
        """Test mesh generation with fidelity governor."""
        from src.services.mesh_governor import select_mesh_preset
        
        # Simulate high load scenario
        with patch('src.services.mesh_governor.settings') as mock_settings:
            mock_settings.feature_mesh_governor = True
            mock_settings.governor_qdepth_drop = 100
            mock_settings.governor_tokens_drop = 6
            
            # High load triggers quality degradation
            preset = select_mesh_preset(queue_depth=150, tokens_in_use=8)
            
            # Should use Point-E with reduced steps
            self.assertEqual(preset["engine"], "point-e")
            self.assertLess(preset["steps"], 64)
            self.assertLess(preset["quality_score"], 1.0)
            self.assertTrue(preset["governor_applied"])

def run_sprint_b_tests():
    """Run all Sprint B tests."""
    print("🧪 Running Sprint B Feature Tests")
    print("=" * 40)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestRequestHedging))
    suite.addTests(loader.loadTestsFromTestCase(TestMeshGovernor))  
    suite.addTests(loader.loadTestsFromTestCase(TestSprintBIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"Ran {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n🎯 Overall: {'✅ PASS' if success else '❌ FAIL'}")
    
    return success

if __name__ == "__main__":
    # Run async tests
    async def run_async_tests():
        test_instance = TestRequestHedging()
        test_instance.setUp()
        
        print("Running async hedging tests...")
        try:
            await test_instance.test_hedging_disabled_single_request()
            print("✅ Hedging disabled test passed")
        except Exception as e:
            print(f"❌ Hedging disabled test failed: {e}")
        
        try:
            await test_instance.test_hedging_primary_wins_fast()
            print("✅ Primary wins fast test passed")
        except Exception as e:
            print(f"❌ Primary wins fast test failed: {e}")
        
        try:
            await test_instance.test_hedging_secondary_wins_race() 
            print("✅ Secondary wins race test passed")
        except Exception as e:
            print(f"❌ Secondary wins race test failed: {e}")
    
    # Run tests
    print("🚀 Sprint B Tests - Hedging & Mesh Governor")
    print("=" * 50)
    
    # Run async tests
    asyncio.run(run_async_tests())
    
    # Run sync tests
    success = run_sprint_b_tests()
    
    exit(0 if success else 1)
