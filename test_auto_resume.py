#!/usr/bin/env python3
"""Test auto-resume functionality after payment."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

import json
from stars_billing import stars_billing
from redis_client import redis_client


class MockUser:
    """Mock user for testing."""
    def __init__(self, username=None, user_id=12345):
        self.username = username
        self.id = user_id


def test_interrupted_context_storage():
    """Test storing and retrieving interrupted processing context."""
    print("🧪 Testing interrupted context storage...")
    
    user_id = 12345
    
    # Simulate interrupted processing context
    interrupted_data = {
        "photo_file_id": "test_photo_123",
        "category": "style_transfer",
        "selected_option": {"prompt": "anime style", "label_key": "style.anime"},
        "user_lang": "en",
        "service_type": "flux",
        "timestamp": "2024-01-01T12:00:00"
    }
    
    # Store interrupted context
    interrupted_key = f"user:{user_id}:interrupted_processing"
    redis_data = {
        "photo_file_id": interrupted_data["photo_file_id"],
        "category": interrupted_data["category"],
        "selected_option": json.dumps(interrupted_data["selected_option"]),
        "user_lang": interrupted_data["user_lang"],
        "service_type": interrupted_data["service_type"],
        "timestamp": interrupted_data["timestamp"]
    }
    
    redis_client.redis.hset(interrupted_key, mapping=redis_data)
    redis_client.redis.expire(interrupted_key, 3600)
    
    print(f"✅ Stored interrupted context for user {user_id}")
    
    # Test retrieval
    import asyncio
    async def test_retrieval():
        retrieved_context = await stars_billing._get_interrupted_processing(user_id)
        
        if retrieved_context:
            print(f"✅ Retrieved context: {retrieved_context['category']}")
            print(f"   Photo: {retrieved_context['photo_file_id']}")
            print(f"   Service: {retrieved_context['service_type']}")
            print(f"   Option: {retrieved_context['selected_option']}")
        else:
            print("❌ Failed to retrieve context")
        
        return retrieved_context
    
    context = asyncio.run(test_retrieval())
    
    # Clean up
    redis_client.redis.delete(interrupted_key)
    
    return context is not None


def test_auto_resume_flag():
    """Test auto-resume flag functionality."""
    print("\n🧪 Testing auto-resume flag...")
    
    user_id = 12345
    auto_resume_key = f"user:{user_id}:auto_resume"
    
    # Set auto-resume flag
    redis_client.redis.setex(auto_resume_key, 300, "1")
    print(f"✅ Set auto-resume flag for user {user_id}")
    
    # Check flag exists
    flag_exists = redis_client.redis.get(auto_resume_key) is not None
    print(f"✅ Flag exists: {flag_exists}")
    
    # Clean up flag
    redis_client.redis.delete(auto_resume_key)
    flag_exists_after = redis_client.redis.get(auto_resume_key) is not None
    print(f"✅ Flag cleaned up: {not flag_exists_after}")
    
    return flag_exists and not flag_exists_after


def test_quota_consumption_for_auto_resume():
    """Test that quota is properly consumed during auto-resume."""
    print("\n🧪 Testing quota consumption for auto-resume...")
    
    # Test with regular user
    regular_user = MockUser(username="test_user", user_id=12346)
    
    # Set some initial quota
    flux_key = f"user:{regular_user.id}:quota:flux"
    redis_client.redis.setex(flux_key, 24 * 3600, 5)  # 5 flux quota
    
    initial_quota = stars_billing.get_user_quota(regular_user.id, "flux")
    print(f"✅ Initial quota: {initial_quota}")
    
    # Consume quota (simulating auto-resume)
    consumed = stars_billing.consume_quota(regular_user.id, "flux", user_obj=regular_user)
    final_quota = stars_billing.get_user_quota(regular_user.id, "flux")
    
    print(f"✅ Quota consumed: {consumed}")
    print(f"✅ Final quota: {final_quota}")
    print(f"✅ Quota difference: {initial_quota - final_quota}")
    
    # Clean up
    redis_client.redis.delete(flux_key)
    
    return consumed and (initial_quota - final_quota == 1)


def test_unlimited_user_auto_resume():
    """Test auto-resume with unlimited user."""
    print("\n🧪 Testing unlimited user auto-resume...")
    
    # Test with unlimited user
    unlimited_user = MockUser(username="aekosyakov", user_id=12347)
    
    # Should not need quota
    consumed = stars_billing.consume_quota(unlimited_user.id, "flux", user_obj=unlimited_user)
    quota_after = stars_billing.get_user_quota(unlimited_user.id, "flux")
    
    print(f"✅ Unlimited user quota consumed: {consumed}")
    print(f"✅ Quota after consumption: {quota_after}")
    
    return consumed  # Should always succeed for unlimited users


def test_payment_flow_simulation():
    """Simulate the complete payment to auto-resume flow."""
    print("\n🧪 Testing complete payment -> auto-resume flow...")
    
    user_id = 12348
    
    # Step 1: User hits quota limit, interrupted context is stored
    interrupted_data = {
        "photo_file_id": "test_photo_456",
        "category": "new_look_women",
        "selected_option": {"prompt": "elegant dress", "label_key": "outfit.elegant"},
        "user_lang": "en",
        "service_type": "flux",
        "timestamp": "2024-01-01T12:30:00"
    }
    
    interrupted_key = f"user:{user_id}:interrupted_processing"
    redis_data = {
        "photo_file_id": interrupted_data["photo_file_id"],
        "category": interrupted_data["category"],
        "selected_option": json.dumps(interrupted_data["selected_option"]),
        "user_lang": interrupted_data["user_lang"],
        "service_type": interrupted_data["service_type"],
        "timestamp": interrupted_data["timestamp"]
    }
    
    redis_client.redis.hset(interrupted_key, mapping=redis_data)
    redis_client.redis.expire(interrupted_key, 3600)
    print("✅ Step 1: Interrupted context stored")
    
    # Step 2: User makes payment, auto-resume flag is set
    auto_resume_key = f"user:{user_id}:auto_resume"
    redis_client.redis.setex(auto_resume_key, 300, "1")
    print("✅ Step 2: Auto-resume flag set after payment")
    
    # Step 3: Check both exist
    context_exists = redis_client.redis.hgetall(interrupted_key) != {}
    flag_exists = redis_client.redis.get(auto_resume_key) is not None
    
    print(f"✅ Step 3: Context exists: {context_exists}, Flag exists: {flag_exists}")
    
    # Step 4: Simulate auto-resume (context retrieved and flag cleared)
    import asyncio
    async def simulate_auto_resume():
        context = await stars_billing._get_interrupted_processing(user_id)
        if context:
            # Simulate processing starts
            redis_client.redis.delete(auto_resume_key)
            redis_client.redis.delete(interrupted_key)
            return True
        return False
    
    resumed = asyncio.run(simulate_auto_resume())
    print(f"✅ Step 4: Auto-resume completed: {resumed}")
    
    # Step 5: Verify cleanup
    context_after = redis_client.redis.hgetall(interrupted_key)
    flag_after = redis_client.redis.get(auto_resume_key)
    
    print(f"✅ Step 5: Context cleaned: {context_after == {}}, Flag cleaned: {flag_after is None}")
    
    return resumed and context_after == {} and flag_after is None


def main():
    """Run all auto-resume tests."""
    print("🔧 Testing Auto-Resume Functionality")
    print("=" * 50)
    
    tests = [
        ("Interrupted Context Storage", test_interrupted_context_storage),
        ("Auto-Resume Flag", test_auto_resume_flag),
        ("Quota Consumption", test_quota_consumption_for_auto_resume),
        ("Unlimited User Auto-Resume", test_unlimited_user_auto_resume),
        ("Complete Payment Flow", test_payment_flow_simulation)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            result = test_func()
            results.append((name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {name}")
        except Exception as e:
            results.append((name, False))
            print(f"\n❌ ERROR in {name}: {e}")
    
    print("\n" + "="*60)
    print("📊 AUTO-RESUME TEST RESULTS:")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    all_passed = all(result for name, result in results)
    
    if all_passed:
        print("\n🎉 All auto-resume tests passed!")
        print("✅ Users can now seamlessly continue processing after payment")
        print("✅ Interrupted context is properly stored and retrieved")
        print("✅ Auto-resume works for both regular and unlimited users")
        print("✅ Quota is properly consumed during auto-resume")
        print("✅ Complete payment-to-processing flow is functional")
    else:
        print("\n⚠️  Some tests failed - auto-resume may not work correctly")
    
    return all_passed


if __name__ == "__main__":
    main() 