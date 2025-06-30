#!/usr/bin/env python3
"""
Test localization to debug the translation issue
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from localization import L

def test_translations():
    """Test if translations are working properly"""
    
    # Test both languages
    for lang in ['en', 'ru']:
        print(f"\n=== Testing {lang.upper()} ===")
        
        # Test basic button translations
        print(f"btn.retry: '{L.get('btn.retry', lang)}'")
        print(f"btn.animate: '{L.get('btn.animate', lang)}'")
        print(f"btn.new_photo: '{L.get('btn.new_photo', lang)}'")
        print(f"btn.back: '{L.get('btn.back', lang)}'")
        
        # Test if missing keys return the key itself
        print(f"missing.key: '{L.get('missing.key', lang)}'")

if __name__ == "__main__":
    test_translations() 