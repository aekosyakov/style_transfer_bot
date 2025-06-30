#!/usr/bin/env python3
"""
Quick test to see prompt generation examples.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('STYLE_TRANSFER_BOT_TOKEN', 'test_token')
os.environ.setdefault('REPLICATE_API_TOKEN', 'test_token')

from src.dresses import dress_generator
from src.mens_outfits import mens_outfit_generator
from src.mens_hairstyles import mens_hairstyle_generator
from src.womens_hairstyles import womens_hairstyle_generator
from src.prompt_variations import PromptVariationGenerator

import logging
logging.basicConfig(level=logging.WARNING)

def quick_test():
    print("🚀 QUICK PROMPT GENERATION TEST")
    print("=" * 50)
    
    # Women's dresses
    print("\n👗 WOMEN'S DRESS EXAMPLES:")
    for i in range(3):
        prompt = dress_generator.get_random_dress(include_color=True, include_material=True)
        print(f"   {i+1}: {prompt}")
    
    # Men's outfits
    print("\n👔 MEN'S OUTFIT EXAMPLES:")
    for i in range(3):
        prompt = mens_outfit_generator.get_random_outfit(include_color=True, include_material=True)
        print(f"   {i+1}: {prompt}")
    
    # Women's hairstyles
    print("\n💇‍♀️ WOMEN'S HAIRSTYLE EXAMPLES:")
    for i in range(3):
        prompt = womens_hairstyle_generator.get_random_hairstyle(include_color=True)
        print(f"   {i+1}: {prompt}")
    
    # Men's hairstyles
    print("\n💈 MEN'S HAIRSTYLE EXAMPLES:")
    for i in range(3):
        prompt = mens_hairstyle_generator.get_random_hairstyle(include_color=True)
        print(f"   {i+1}: {prompt}")
    
    # Variation system
    print("\n🔄 VARIATION SYSTEM EXAMPLES:")
    pv = PromptVariationGenerator()
    
    dress_variation = pv._generate_dress_variation("dress.random", "RANDOM_DRESS", preserve_gender='women')
    print(f"   RANDOM_DRESS -> {dress_variation}")
    
    mens_variation = pv._generate_dress_variation("mens.random", "RANDOM_MENS_OUTFIT", preserve_gender='men')
    print(f"   RANDOM_MENS_OUTFIT -> {mens_variation}")
    
    hair_variation = pv._generate_hairstyle_variation("hair.random", "RANDOM_WOMENS_HAIRSTYLE")
    print(f"   RANDOM_WOMENS_HAIRSTYLE -> {hair_variation}")
    
    print("\n✅ Quick test complete!")

if __name__ == "__main__":
    quick_test()
