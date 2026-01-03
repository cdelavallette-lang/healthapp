"""
Test script to verify modifier functionality
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from chemistry.soap_calculator import SoapChemistry

# Initialize chemistry calculator
base_path = os.path.dirname(__file__)
oils_path = os.path.join(base_path, 'data', 'oils.json')
modifiers_path = os.path.join(base_path, 'data', 'modifiers.json')

chemistry = SoapChemistry(oils_path, modifiers_path)

# Test basic recipe with citric acid
oil_weights = {
    'Coconut Oil': 200.0,  # grams
    'Olive Oil': 400.0,
    'Palm Oil': 200.0
}

modifiers = {
    'Citric Acid': 8.0  # 1% of 800g oils
}

print("Test Recipe with Citric Acid")
print("=" * 50)
print(f"\nOils: {oil_weights}")
print(f"Modifiers: {modifiers}")

# Calculate lye with modifiers
lye_amount, lye_adjustment = chemistry.calculate_lye_amount(
    oil_weights, 
    superfat_percent=5.0,
    modifiers=modifiers
)

print(f"\nLye amount (base): {lye_amount}g")
print(f"Lye adjustment (for citric acid): {lye_adjustment}g")
print(f"Total lye needed: {lye_amount + lye_adjustment}g")

# Test modifier info
print("\n" + "=" * 50)
print("Available Modifiers:")
print("=" * 50)
for modifier in chemistry.get_available_modifiers():
    info = chemistry.get_modifier_info(modifier)
    print(f"\n{modifier}:")
    print(f"  Category: {info.get('category')}")
    print(f"  Typical usage: {info.get('typical_usage_percent', 'N/A')}%")
    if 'lye_adjustment_note' in info:
        print(f"  ⚠ {info['lye_adjustment_note']}")

print("\n" + "=" * 50)
print("Test completed successfully!")
