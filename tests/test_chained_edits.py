#!/usr/bin/env python3
"""
Test script to help debug chained edit issues.
This simulates the workflow: Upload → Edit Men's Outfit → Edit → Edit Men's Hairstyle
"""

import os
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up minimal environment
os.environ.setdefault('STYLE_TRANSFER_BOT_TOKEN', 'test_token')
os.environ.setdefault('REPLICATE_API_TOKEN', 'test_token')

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simulate_chained_edit_workflow():
    """Simulate the problematic workflow to understand the issue."""
    
    print("🔍 SIMULATING CHAINED EDIT WORKFLOW")
    print("=" * 60)
    
    # Simulate context data like Telegram bot would have
    context_data = {
        'current_photo': 'initial_photo_file_id_12345',
        'last_processing': None
    }
    
    print(f"\n📷 STEP 1: Initial photo upload")
    print(f"   - current_photo: {context_data['current_photo']}")
    print(f"   - last_processing: {context_data['last_processing']}")
    
    # Simulate men's outfit edit
    print(f"\n👔 STEP 2: User selects men's outfit edit")
    mens_outfit_option = {
        'label_key': 'mens.random',
        'prompt': 'RANDOM_MENS_OUTFIT'
    }
    
    # Simulate generation manager storing processing context
    context_data['last_processing'] = {
        'photo_file_id': context_data['current_photo'],  # Uses initial photo
        'category': 'new_look_men',
        'selected_option': mens_outfit_option,
        'user_id': 12345,
        'user_lang': 'en',
        'gender': 'men'
    }
    
    print(f"   - Processing with photo_file_id: {context_data['last_processing']['photo_file_id']}")
    print(f"   - Category: {context_data['last_processing']['category']}")
    print(f"   - Option: {mens_outfit_option}")
    
    # Simulate successful generation and context update
    result_photo_id = 'mens_outfit_result_file_id_67890'
    print(f"\n✅ STEP 3: Men's outfit generation completes")
    print(f"   - Result photo_file_id: {result_photo_id}")
    
    # Context should be updated after generation
    context_data['current_photo'] = result_photo_id
    context_data['last_processing']['photo_file_id'] = result_photo_id
    
    print(f"   - Updated current_photo: {context_data['current_photo']}")
    print(f"   - Updated last_processing photo_file_id: {context_data['last_processing']['photo_file_id']}")
    
    # Simulate user clicking Edit button
    print(f"\n✏️ STEP 4: User clicks Edit button")
    
    # Edit button should extract photo from result message and update context
    # In real bot, this would be: update.callback_query.message.photo[-1].file_id
    edit_extracted_photo_id = result_photo_id  # Should be same as result
    
    print(f"   - Edit button extracts photo_file_id: {edit_extracted_photo_id}")
    
    # Update context (like _handle_restart does)
    context_data['current_photo'] = edit_extracted_photo_id
    if context_data['last_processing']:
        context_data['last_processing']['photo_file_id'] = edit_extracted_photo_id
    
    print(f"   - Updated current_photo: {context_data['current_photo']}")
    print(f"   - Updated last_processing photo_file_id: {context_data['last_processing']['photo_file_id']}")
    
    # Simulate user selecting men's hairstyle
    print(f"\n💈 STEP 5: User selects men's hairstyle edit")
    mens_hair_option = {
        'label_key': 'hair.men_random',
        'prompt': 'RANDOM_MENS_HAIRSTYLE'
    }
    
    # Check what photo_file_id would be used
    photo_for_hair_edit = context_data.get('current_photo')
    print(f"   - Using photo_file_id for hairstyle edit: {photo_for_hair_edit}")
    print(f"   - Expected (should be result from men's outfit): {result_photo_id}")
    print(f"   - Match: {photo_for_hair_edit == result_photo_id}")
    
    # Simulate the issue scenarios
    print(f"\n🚨 POTENTIAL ISSUE SCENARIOS:")
    
    print(f"\n   Scenario 1: File ID mismatch")
    if photo_for_hair_edit != result_photo_id:
        print(f"      ❌ photo_file_id mismatch!")
        print(f"      - Expected: {result_photo_id}")
        print(f"      - Got: {photo_for_hair_edit}")
    else:
        print(f"      ✅ photo_file_id matches correctly")
    
    print(f"\n   Scenario 2: Telegram file ID expiration")
    print(f"      - If Telegram file_id expires between operations")
    print(f"      - This would cause 'wrong remote file identifier' errors")
    print(f"      - Check logs for: 'TELEGRAM_FILE_ID_ERROR'")
    
    print(f"\n   Scenario 3: Photo compression/re-encoding")
    print(f"      - When bot sends result image, Telegram might compress it")
    print(f"      - This creates a new file_id different from API result")
    print(f"      - Edit button extracts the compressed version's file_id")
    print(f"      - But context update uses the original API result file_id")
    
    print(f"\n   Scenario 4: Context corruption")
    print(f"      - If context.user_data gets corrupted between operations")
    print(f"      - Check logs for: 'Context user_data keys'")
    
    print(f"\n📝 DEBUGGING RECOMMENDATIONS:")
    print(f"   1. Check logs for 'EDIT_BUTTON_DEBUG' messages")
    print(f"   2. Check logs for 'CONTEXT_UPDATE_DEBUG' messages") 
    print(f"   3. Check logs for 'PHOTO_RETRIEVAL_DEBUG' messages")
    print(f"   4. Look for file_id mismatches between Edit extraction and context")
    print(f"   5. Check for Telegram file_id errors")
    print(f"   6. Verify that both current_photo and last_processing are updated consistently")


def test_file_id_patterns():
    """Test to understand Telegram file_id patterns."""
    
    print(f"\n🔬 TELEGRAM FILE_ID PATTERN ANALYSIS")
    print("=" * 60)
    
    # Examples of actual Telegram file_ids (anonymized)
    example_file_ids = [
        "AgACAgIAAxkBAAICHmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # Photo from user upload
        "AgACAgIAAxkBAAICJmYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",  # Photo sent by bot (result)
        "BAADBAADZAIAAkKiuEjaY7HLf7Va2wAE",                    # Document/file
    ]
    
    print(f"\n📋 File ID characteristics:")
    for i, file_id in enumerate(example_file_ids, 1):
        print(f"   Example {i}: {file_id}")
        print(f"     - Length: {len(file_id)}")
        print(f"     - Starts with: {file_id[:10]}...")
        print(f"     - Type hint: {'Photo' if file_id.startswith('AgAC') else 'Document' if file_id.startswith('BAAD') else 'Unknown'}")
    
    print(f"\n🔍 Key observations:")
    print(f"   - User uploaded photos: Usually start with 'AgAC'")
    print(f"   - Bot sent photos: May have different prefixes")
    print(f"   - Length typically 50-60 characters")
    print(f"   - Changes when photo is compressed/processed by Telegram")


def suggest_fixes():
    """Suggest potential fixes for the chained edit issue."""
    
    print(f"\n🔧 SUGGESTED FIXES")
    print("=" * 60)
    
    print(f"\n1. **Enhanced File ID Validation**")
    print(f"   - Add validation before using file_id")
    print(f"   - Catch and handle expired file_id errors gracefully")
    print(f"   - Fallback to requesting new photo upload")
    
    print(f"\n2. **Consistent Context Updates**")
    print(f"   - Ensure both current_photo and last_processing are always updated together")
    print(f"   - Add validation that extracted file_id matches expected patterns")
    
    print(f"\n3. **Retry Mechanism**")
    print(f"   - If file_id fails, try alternative file_ids from photo array")
    print(f"   - Implement automatic retry with fresh photo upload request")
    
    print(f"\n4. **Better Error Messages**")
    print(f"   - Show specific error for chained edit failures")
    print(f"   - Guide user to upload fresh photo if needed")
    
    print(f"\n5. **File ID Caching Strategy**")
    print(f"   - Store multiple file_id versions (original + compressed)")
    print(f"   - Try both when one fails")


def main():
    """Main function."""
    print("🚀 CHAINED EDIT DEBUGGING TOOL")
    print("🎯 Analyzing: Upload → Men's Outfit → Edit → Men's Hairstyle workflow")
    
    simulate_chained_edit_workflow()
    test_file_id_patterns()
    suggest_fixes()
    
    print(f"\n✅ DEBUGGING ANALYSIS COMPLETE!")
    print(f"\n💡 Next steps:")
    print(f"   1. Deploy the enhanced logging")
    print(f"   2. Try the problematic workflow")
    print(f"   3. Check logs for the debug messages")
    print(f"   4. Look for file_id mismatches or Telegram errors")


if __name__ == "__main__":
    main() 