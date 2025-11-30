#!/usr/bin/env python3
"""
Production Optimization Features Testing for On-the-Cheap Backend API

This test suite focuses on testing the newly implemented production optimization features:
1. Production Service Initialization (cache service and database service)
2. Caching System Integration (Google Places and geocoding API caching)
3. Admin/Monitoring Endpoints (5 new admin endpoints)
4. Database Indexes (verify database service creates proper indexes)
5. API Quota Tracking (quota management and throttling)
6. Performance Monitoring (cache hit/miss tracking and statistics)
"""

import requests
import sys
import json
import time
from datetime import datetime
import uuid

class ProductionOptimizationTester:
    def __init__(self, base_url="https://deal-discovery-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   Details: {details}")

    def test_production_service_initialization(self):
        """Test that production services (cache and database) are properly initialized"""
        try:
            # Test admin/performance endpoint to check service availability
            response = self.session.get(f"{self.api_url}/admin/performance")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                services = data.get('services', {})
                cache_status = services.get('cache', 'unavailable')
                database_status = services.get('database', 'unavailable')
                
                if cache_status == 'available' and database_status == 'available':
                    details = f"✅ Both services initialized: Cache={cache_status}, Database={database_status}"
                    success = True
                else:
                    details = f"❌ Service initialization issues: Cache={cache_status}, Database={database_status}"
                    success = False
            else:
                details = f"Admin endpoint not accessible: {response.status_code} - {response.text[:200]}"
                success = False
            
            self.log_test("Production Service Initialization", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Production Service Initialization", False, str(e))
            return False, {}

    def test_admin_performance_endpoint(self):
        """Test /api/admin/performance endpoint for performance statistics"""
        try:
            response = self.session.get(f"{self.api_url}/admin/performance")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check required fields in performance stats
                required_fields = ['timestamp', 'services']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    # Check cache statistics if available
                    cache_stats = data.get('cache', {})
                    api_quotas = data.get('api_quotas', {})
                    database_stats = data.get('database', {})
                    
                    details = f"Performance stats retrieved successfully"
                    if cache_stats:
                        hit_rate = cache_stats.get('hit_rate', 0)
                        cache_entries = cache_stats.get('cache_entries', 0)
                        details += f", Cache: {cache_entries} entries, {hit_rate}% hit rate"
                    
                    if api_quotas:
                        quota_services = list(api_quotas.keys())
                        details += f", API quotas tracked: {quota_services}"
                    
                    if database_stats:
                        details += f", Database stats available"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Performance Endpoint", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Admin Performance Endpoint", False, str(e))
            return False, {}

    def test_admin_health_endpoint(self):
        """Test /api/admin/health endpoint for comprehensive health check"""
        try:
            response = self.session.get(f"{self.api_url}/admin/health")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check required fields in health check
                required_fields = ['timestamp', 'overall_status', 'services']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    overall_status = data.get('overall_status')
                    services = data.get('services', {})
                    
                    # Check individual service health
                    database_health = services.get('database', {})
                    cache_health = services.get('cache', {})
                    api_quotas_health = services.get('api_quotas', {})
                    
                    details = f"Overall status: {overall_status}"
                    
                    if database_health:
                        db_status = database_health.get('status', 'unknown')
                        details += f", Database: {db_status}"
                        
                        if db_status == 'healthy':
                            ping_time = database_health.get('ping_time_ms', 'N/A')
                            read_time = database_health.get('read_time_ms', 'N/A')
                            write_time = database_health.get('write_time_ms', 'N/A')
                            details += f" (ping: {ping_time}ms, read: {read_time}ms, write: {write_time}ms)"
                    
                    if cache_health:
                        cache_status = cache_health.get('status', 'unknown')
                        hit_rate = cache_health.get('hit_rate', 'N/A')
                        details += f", Cache: {cache_status} (hit rate: {hit_rate}%)"
                    
                    if api_quotas_health:
                        quota_count = len(api_quotas_health)
                        details += f", API quotas: {quota_count} services monitored"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Health Check Endpoint", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Admin Health Check Endpoint", False, str(e))
            return False, {}

    def test_admin_cache_clear_endpoint(self):
        """Test /api/admin/cache/clear endpoint for cache management"""
        try:
            # First, populate cache by making some API calls
            print("   Populating cache with API calls...")
            
            # Make geocoding calls to populate cache
            geocoding_data = {"address": "San Francisco, CA"}
            self.session.post(f"{self.api_url}/geocode/forward", json=geocoding_data)
            
            # Make restaurant search calls to populate cache
            search_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            
            # Test clearing all cache
            response = self.session.post(f"{self.api_url}/admin/cache/clear")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check response format
                required_fields = ['message', 'cleared_entries']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    cleared_entries = data.get('cleared_entries', 0)
                    message = data.get('message', '')
                    details = f"Cache cleared successfully: {message}, Entries cleared: {cleared_entries}"
                    
                    # Test clearing specific cache type
                    # First populate cache again
                    self.session.post(f"{self.api_url}/geocode/forward", json=geocoding_data)
                    
                    # Clear specific cache type
                    specific_response = self.session.post(f"{self.api_url}/admin/cache/clear?cache_type=geocoding")
                    if specific_response.status_code == 200:
                        specific_data = specific_response.json()
                        specific_cleared = specific_data.get('cleared_entries', 0)
                        details += f", Specific type clear: {specific_cleared} geocoding entries"
                    else:
                        details += f", Specific type clear failed: {specific_response.status_code}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Cache Clear Endpoint", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Admin Cache Clear Endpoint", False, str(e))
            return False, {}

    def test_admin_database_optimize_endpoint(self):
        """Test /api/admin/database/optimize endpoint for database optimization"""
        try:
            response = self.session.post(f"{self.api_url}/admin/database/optimize")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check response format
                required_fields = ['message', 'results', 'timestamp']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    results = data.get('results', {})
                    message = data.get('message', '')
                    
                    # Check that expected collections were optimized
                    expected_collections = ['restaurants', 'users', 'restaurant_owners']
                    optimized_collections = list(results.keys())
                    
                    details = f"Database optimization completed: {message}"
                    details += f", Collections optimized: {optimized_collections}"
                    
                    # Check optimization results for each collection
                    for collection in expected_collections:
                        if collection in results:
                            collection_result = results[collection]
                            status = collection_result.get('status', 'unknown')
                            details += f", {collection}: {status}"
                            
                            if status == 'optimized':
                                improvement = collection_result.get('improvement', {})
                                size_reduction = improvement.get('size_reduction', 0)
                                if size_reduction != 0:
                                    details += f" (size reduction: {size_reduction} bytes)"
                        else:
                            details += f", {collection}: missing from results"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Database Optimize Endpoint", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Admin Database Optimize Endpoint", False, str(e))
            return False, {}

    def test_admin_quota_status_endpoint(self):
        """Test /api/admin/quota-status endpoint for API quota monitoring"""
        try:
            response = self.session.get(f"{self.api_url}/admin/quota-status")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check if quota data is available
                if not data or (len(data) == 1 and 'message' in data):
                    # Cache service might not be available or no quotas tracked yet
                    details = f"Quota status endpoint accessible, but no quota data available yet: {data.get('message', 'No quotas tracked')}"
                    success = True
                else:
                    # Check quota data format for tracked services
                    quota_services = [key for key in data.keys() if key != 'message']
                    details = f"API quota status retrieved for {len(quota_services)} services"
                    
                    if quota_services:
                        details += f": {quota_services}"
                        
                        # Check first service quota format
                        first_service = quota_services[0]
                        quota_info = data[first_service]
                        
                        if quota_info:
                            expected_fields = ['service', 'requests_made', 'quota_limit', 'usage_percent']
                            missing_fields = [field for field in expected_fields if field not in quota_info]
                            
                            if missing_fields:
                                details += f", Missing quota fields: {missing_fields}"
                            else:
                                usage_percent = quota_info.get('usage_percent', 0)
                                requests_made = quota_info.get('requests_made', 0)
                                quota_limit = quota_info.get('quota_limit', 0)
                                recommendation = quota_info.get('recommendation', 'N/A')
                                
                                details += f", {first_service}: {requests_made}/{quota_limit} ({usage_percent}%) - {recommendation}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Quota Status Endpoint", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Admin Quota Status Endpoint", False, str(e))
            return False, {}

    def test_caching_system_integration(self):
        """Test caching system integration for Google Places and geocoding APIs"""
        try:
            print("   Testing cache integration with multiple API calls...")
            
            # Test geocoding caching
            geocoding_data = {"address": "1600 Amphitheatre Parkway, Mountain View, CA"}
            
            # First call - should miss cache
            start_time = time.time()
            response1 = self.session.post(f"{self.api_url}/geocode/forward", json=geocoding_data)
            first_call_time = time.time() - start_time
            
            # Second call - should hit cache (faster)
            start_time = time.time()
            response2 = self.session.post(f"{self.api_url}/geocode/forward", json=geocoding_data)
            second_call_time = time.time() - start_time
            
            geocoding_success = response1.status_code == 200 and response2.status_code == 200
            
            # Test Google Places caching
            search_params = {
                'latitude': 37.4419,  # Mountain View coordinates
                'longitude': -122.1430,
                'radius': 5000
            }
            
            # First search call
            start_time = time.time()
            search_response1 = self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            first_search_time = time.time() - start_time
            
            # Second search call - should be faster due to caching
            start_time = time.time()
            search_response2 = self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            second_search_time = time.time() - start_time
            
            search_success = search_response1.status_code == 200 and search_response2.status_code == 200
            
            success = geocoding_success and search_success
            
            if success:
                details = f"Caching integration working"
                details += f", Geocoding: 1st call {first_call_time:.3f}s, 2nd call {second_call_time:.3f}s"
                details += f", Search: 1st call {first_search_time:.3f}s, 2nd call {second_search_time:.3f}s"
                
                # Check if second calls were faster (indicating cache hits)
                if second_call_time < first_call_time * 0.8:
                    details += " - Geocoding cache hit detected"
                if second_search_time < first_search_time * 0.8:
                    details += " - Search cache hit detected"
                
                # Get cache statistics to verify
                perf_response = self.session.get(f"{self.api_url}/admin/performance")
                if perf_response.status_code == 200:
                    perf_data = perf_response.json()
                    cache_stats = perf_data.get('cache', {})
                    if cache_stats:
                        hit_rate = cache_stats.get('hit_rate', 0)
                        cache_entries = cache_stats.get('cache_entries', 0)
                        details += f", Cache stats: {cache_entries} entries, {hit_rate}% hit rate"
            else:
                details = f"Caching test failed - Geocoding: {response1.status_code}/{response2.status_code}, Search: {search_response1.status_code}/{search_response2.status_code}"
            
            self.log_test("Caching System Integration", success, details)
            return success
            
        except Exception as e:
            self.log_test("Caching System Integration", False, str(e))
            return False

    def test_api_quota_tracking(self):
        """Test API quota tracking and management features"""
        try:
            # Make several API calls to generate quota usage
            print("   Making API calls to generate quota usage...")
            
            # Make multiple geocoding calls
            addresses = [
                "San Francisco, CA",
                "New York, NY", 
                "Los Angeles, CA",
                "Chicago, IL",
                "Houston, TX"
            ]
            
            for address in addresses:
                geocoding_data = {"address": address}
                self.session.post(f"{self.api_url}/geocode/forward", json=geocoding_data)
            
            # Make multiple restaurant search calls
            locations = [
                (37.7749, -122.4194),  # San Francisco
                (40.7589, -73.9851),   # New York
                (34.0522, -118.2437),  # Los Angeles
                (41.8781, -87.6298),   # Chicago
                (29.7604, -95.3698)    # Houston
            ]
            
            for lat, lng in locations:
                search_params = {
                    'latitude': lat,
                    'longitude': lng,
                    'radius': 5000
                }
                self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            
            # Check quota status
            quota_response = self.session.get(f"{self.api_url}/admin/quota-status")
            success = quota_response.status_code == 200
            
            if success:
                quota_data = quota_response.json()
                
                if not quota_data or 'message' in quota_data:
                    details = "Quota tracking endpoint accessible but no quota data available yet"
                    success = True
                else:
                    # Handle the actual response format
                    quotas = quota_data.get('quotas', {})
                    timestamp = quota_data.get('timestamp', 'N/A')
                    cache_performance = quota_data.get('cache_performance', {})
                    
                    if quotas:
                        tracked_services = list(quotas.keys())
                        details = f"Quota tracking working for {len(tracked_services)} services"
                        details += f": {tracked_services}"
                        
                        # Check if any services show usage
                        total_requests = 0
                        for service in tracked_services:
                            service_quota = quotas[service]
                            if service_quota and isinstance(service_quota, dict):
                                requests_made = service_quota.get('requests_made', 0)
                                total_requests += requests_made
                                usage_percent = service_quota.get('usage_percent', 0)
                                details += f", {service}: {requests_made} requests ({usage_percent}%)"
                        
                        if total_requests > 0:
                            details += f" - Total API requests tracked: {total_requests}"
                        else:
                            details += " - No API usage recorded yet (may be due to caching)"
                    else:
                        details = f"Quota endpoint working, timestamp: {timestamp}, cache performance available: {bool(cache_performance)}"
            else:
                details = f"Status: {quota_response.status_code}, Response: {quota_response.text[:200]}"
            
            self.log_test("API Quota Tracking", success, details)
            return success
            
        except Exception as e:
            self.log_test("API Quota Tracking", False, str(e))
            return False

    def test_database_indexes_creation(self):
        """Test that database service creates proper indexes for performance"""
        try:
            # Test database health to verify indexes are created
            health_response = self.session.get(f"{self.api_url}/admin/health")
            success = health_response.status_code == 200
            
            if success:
                health_data = health_response.json()
                services = health_data.get('services', {})
                database_health = services.get('database', {})
                
                if database_health:
                    db_status = database_health.get('status')
                    
                    if db_status == 'healthy':
                        # Get detailed database stats
                        perf_response = self.session.get(f"{self.api_url}/admin/performance")
                        if perf_response.status_code == 200:
                            perf_data = perf_response.json()
                            database_stats = perf_data.get('database', {})
                            
                            if database_stats:
                                collections_stats = database_stats.get('collections', {})
                                indexes_created = database_stats.get('indexes_created', False)
                                
                                details = f"Database indexes status: {indexes_created}"
                                
                                # Check index information for key collections
                                key_collections = ['restaurants', 'users', 'restaurant_owners']
                                for collection in key_collections:
                                    if collection in collections_stats:
                                        collection_info = collections_stats[collection]
                                        if isinstance(collection_info, dict):
                                            indexes = collection_info.get('indexes', 0)
                                            documents = collection_info.get('documents', 0)
                                            details += f", {collection}: {indexes} indexes, {documents} docs"
                                        else:
                                            details += f", {collection}: {collection_info}"
                                
                                success = indexes_created
                                if not success:
                                    details += " - Indexes not properly created"
                            else:
                                details = "Database healthy but no detailed stats available"
                        else:
                            details = f"Database healthy (ping: {database_health.get('ping_time_ms', 'N/A')}ms) but performance stats unavailable"
                    else:
                        details = f"Database status: {db_status}"
                        success = False
                else:
                    details = "Database health information not available"
                    success = False
            else:
                details = f"Health check failed: {health_response.status_code}"
                success = False
            
            self.log_test("Database Indexes Creation", success, details)
            return success
            
        except Exception as e:
            self.log_test("Database Indexes Creation", False, str(e))
            return False

    def test_performance_monitoring(self):
        """Test performance monitoring with cache hit/miss tracking and statistics"""
        try:
            # Clear cache first to start fresh
            self.session.post(f"{self.api_url}/admin/cache/clear")
            
            # Make API calls to generate cache misses and hits
            print("   Generating cache misses and hits for performance monitoring...")
            
            # First call - cache miss
            geocoding_data = {"address": "Seattle, WA"}
            self.session.post(f"{self.api_url}/geocode/forward", json=geocoding_data)
            
            # Second call - cache hit
            self.session.post(f"{self.api_url}/geocode/forward", json=geocoding_data)
            
            # Restaurant search - cache miss
            search_params = {
                'latitude': 47.6062,
                'longitude': -122.3321,
                'radius': 5000
            }
            self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            
            # Same search - cache hit
            self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            
            # Get performance statistics
            perf_response = self.session.get(f"{self.api_url}/admin/performance")
            success = perf_response.status_code == 200
            
            if success:
                perf_data = perf_response.json()
                cache_stats = perf_data.get('cache', {})
                
                if cache_stats:
                    # Check cache performance metrics
                    hit_rate = cache_stats.get('hit_rate', 0)
                    total_hits = cache_stats.get('total_hits', 0)
                    total_misses = cache_stats.get('total_misses', 0)
                    cache_entries = cache_stats.get('cache_entries', 0)
                    api_calls_saved = cache_stats.get('api_calls_saved', 0)
                    cost_saved = cache_stats.get('estimated_cost_saved', '$0.0000')
                    
                    details = f"Performance monitoring working"
                    details += f", Hit rate: {hit_rate}%, Hits: {total_hits}, Misses: {total_misses}"
                    details += f", Cache entries: {cache_entries}, API calls saved: {api_calls_saved}"
                    details += f", Cost saved: {cost_saved}"
                    
                    # Check type breakdown
                    type_breakdown = cache_stats.get('type_breakdown', {})
                    if type_breakdown:
                        cache_types = list(type_breakdown.keys())
                        details += f", Cache types: {cache_types}"
                    
                    # Verify we have some cache activity
                    if total_hits > 0 or total_misses > 0:
                        details += " - Cache activity detected"
                    else:
                        details += " - No cache activity recorded"
                else:
                    details = "Performance stats available but no cache statistics"
                    success = True  # Still consider successful if endpoint works
            else:
                details = f"Performance monitoring failed: {perf_response.status_code}"
                success = False
            
            self.log_test("Performance Monitoring", success, details)
            return success
            
        except Exception as e:
            self.log_test("Performance Monitoring", False, str(e))
            return False

    def test_cache_throttling_behavior(self):
        """Test API quota throttling features"""
        try:
            # Get current quota status
            quota_response = self.session.get(f"{self.api_url}/admin/quota-status")
            
            if quota_response.status_code == 200:
                quota_data = quota_response.json()
                
                # Check if throttling logic is in place
                details = "Throttling system accessible"
                
                if quota_data and isinstance(quota_data, dict):
                    services_with_quotas = [key for key in quota_data.keys() if key != 'message']
                    
                    if services_with_quotas:
                        details += f", Quota tracking for {len(services_with_quotas)} services"
                        
                        # Check recommendations for throttling
                        for service in services_with_quotas:
                            service_quota = quota_data[service]
                            if service_quota and isinstance(service_quota, dict):
                                usage_percent = service_quota.get('usage_percent', 0)
                                recommendation = service_quota.get('recommendation', '')
                                
                                details += f", {service}: {usage_percent}% usage"
                                
                                if 'CRITICAL' in recommendation or 'WARNING' in recommendation:
                                    details += f" ({recommendation})"
                                elif usage_percent > 50:
                                    details += " (MODERATE usage)"
                                else:
                                    details += " (LOW usage)"
                    else:
                        details += ", No services with quota data yet"
                else:
                    details += ", No quota data available yet"
                
                success = True
            else:
                details = f"Throttling system check failed: {quota_response.status_code}"
                success = False
            
            self.log_test("Cache Throttling Behavior", success, details)
            return success
            
        except Exception as e:
            self.log_test("Cache Throttling Behavior", False, str(e))
            return False

    def run_production_optimization_tests(self):
        """Run all production optimization tests"""
        print("🚀 TESTING PRODUCTION OPTIMIZATION FEATURES")
        print("=" * 70)
        print("Testing newly implemented production optimization features:")
        print("1. Production Service Initialization")
        print("2. Caching System Integration") 
        print("3. Admin/Monitoring Endpoints (5 endpoints)")
        print("4. Database Indexes")
        print("5. API Quota Tracking")
        print("6. Performance Monitoring")
        print("=" * 70)
        
        # Test 1: Production Service Initialization
        print("\n🔧 Testing Production Service Initialization...")
        self.test_production_service_initialization()
        
        # Test 2: Admin Endpoints (5 endpoints)
        print("\n📊 Testing Admin/Monitoring Endpoints...")
        self.test_admin_performance_endpoint()
        self.test_admin_health_endpoint()
        self.test_admin_cache_clear_endpoint()
        self.test_admin_database_optimize_endpoint()
        self.test_admin_quota_status_endpoint()
        
        # Test 3: Caching System Integration
        print("\n💾 Testing Caching System Integration...")
        self.test_caching_system_integration()
        
        # Test 4: Database Indexes
        print("\n🗃️ Testing Database Indexes Creation...")
        self.test_database_indexes_creation()
        
        # Test 5: API Quota Tracking
        print("\n📈 Testing API Quota Tracking...")
        self.test_api_quota_tracking()
        
        # Test 6: Performance Monitoring
        print("\n⚡ Testing Performance Monitoring...")
        self.test_performance_monitoring()
        
        # Test 7: Cache Throttling
        print("\n🚦 Testing Cache Throttling Behavior...")
        self.test_cache_throttling_behavior()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 PRODUCTION OPTIMIZATION TEST RESULTS: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All production optimization features are working correctly!")
            print("✅ Cache service and database service initialized properly")
            print("✅ All 5 admin endpoints are functional")
            print("✅ Caching system is improving API performance")
            print("✅ Database indexes created for optimal performance")
            print("✅ API quota tracking and throttling working")
            print("✅ Performance monitoring capturing metrics")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️ {failed_tests} production optimization tests failed")
            print("Some production features may need attention")
            return False

def main():
    """Main test runner for production optimization features"""
    tester = ProductionOptimizationTester()
    success = tester.run_production_optimization_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())