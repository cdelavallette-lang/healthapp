"""
Test script to diagnose modifier flow through the application
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from chemistry.soap_calculator import SoapChemistry
from models.recipe import Recipe

print("=" * 60)
print("MODIFIER FLOW TEST")
print("=" * 60)

# Test 1: Load chemistry and check modifiers database
print("\n1. Testing SoapChemistry initialization...")
chemistry = SoapChemistry(
    oils_database_path='data/oils.json',
    modifiers_database_path='data/modifiers.json'
)

available_modifiers = chemistry.get_available_modifiers()
print(f"   Available modifiers: {available_modifiers}")
print(f"   Count: {len(available_modifiers)}")

# Test 2: Get info for Citric Acid
print("\n2. Testing get_modifier_info for 'Citric Acid'...")
citric_info = chemistry.get_modifier_info('Citric Acid')
if citric_info:
    print(f"   Found: {citric_info['name']}")
    print(f"   Category: {citric_info.get('category', 'N/A')}")
    print(f"   Lye adjustment factor: {citric_info.get('lye_adjustment_factor', 'N/A')}")
else:
    print("   ERROR: Citric Acid not found!")

# Test 3: Create a simple recipe with oils
print("\n3. Creating test recipe with oils...")
test_oils = {
    'Olive Oil': 500.0,  # 500g
    'Coconut Oil': 300.0,  # 300g
    'Palm Oil': 200.0  # 200g
}
total_oils = sum(test_oils.values())
print(f"   Total oils: {total_oils}g")

# Test 4: Calculate lye with modifiers
print("\n4. Testing lye calculation with Citric Acid...")
modifiers = {'Citric Acid': 10.0}  # 10g citric acid
print(f"   Modifiers: {modifiers}")

# Debug the calculation
print("\n   Debug lye calculation:")
for mod_name, amount in modifiers.items():
    print(f"   - Checking modifier: '{mod_name}'")
    print(f"   - In modifiers_db: {mod_name in chemistry.modifiers_db}")
    if mod_name in chemistry.modifiers_db:
        mod_info = chemistry.modifiers_db[mod_name]
        print(f"   - Has lye_adjustment_factor: {'lye_adjustment_factor' in mod_info}")
        if 'lye_adjustment_factor' in mod_info:
            factor = mod_info['lye_adjustment_factor']
            print(f"   - Factor: {factor}")
            print(f"   - Amount: {amount}g")
            print(f"   - Adjustment: {amount * factor}g")

lye_amount, lye_adjustment = chemistry.calculate_lye_amount(test_oils, 5.0, modifiers)
print(f"\n   Base lye: {lye_amount:.2f}g")
print(f"   Lye adjustment: {lye_adjustment:.2f}g")
print(f"   Total lye: {lye_amount + lye_adjustment:.2f}g")
print(f"   Expected adjustment: {10.0 * 0.6:.2f}g (10g citric * 0.6 factor)")

# Test 5: Create Recipe object with modifiers
print("\n5. Creating Recipe object with modifiers...")
recipe = Recipe(
    name="Test Recipe",
    oils=test_oils,
    superfat=5.0,
    lye_concentration=33.0,
    fragrance_percent=3.0,
    modifiers=modifiers
)

print(f"   Recipe name: {recipe.name}")
print(f"   Has modifiers attribute: {hasattr(recipe, 'modifiers')}")
if hasattr(recipe, 'modifiers'):
    print(f"   Modifiers: {recipe.modifiers}")
    print(f"   Modifiers type: {type(recipe.modifiers)}")
    print(f"   Modifiers empty: {not recipe.modifiers}")

# Test 6: Calculate all recipe values
print("\n6. Calculating recipe values...")
recipe.lye_amount, recipe.lye_adjustment = chemistry.calculate_lye_amount(test_oils, 5.0, modifiers)
recipe.water_amount = chemistry.calculate_water_amount(recipe.lye_amount + recipe.lye_adjustment, 33.0)
recipe.fragrance_amount = chemistry.calculate_fragrance_amount(total_oils, 3.0)
recipe.properties = chemistry.calculate_soap_properties(test_oils)
recipe.fatty_acids = chemistry.calculate_fatty_acid_profile(test_oils)

print(f"   Lye: {recipe.lye_amount:.2f}g + {recipe.lye_adjustment:.2f}g = {recipe.lye_amount + recipe.lye_adjustment:.2f}g")
print(f"   Water: {recipe.water_amount:.2f}g")
print(f"   Fragrance: {recipe.fragrance_amount:.2f}g")
print(f"   Modifiers in recipe: {recipe.modifiers}")

# Test 7: Convert to dict and back
print("\n7. Testing recipe serialization...")
recipe_dict = recipe.to_dict()
print(f"   'modifiers' in dict: {'modifiers' in recipe_dict}")
if 'modifiers' in recipe_dict:
    print(f"   Modifiers in dict: {recipe_dict['modifiers']}")

# Test 8: Check PDF export would receive modifiers
print("\n8. Simulating PDF export check...")
has_additives = recipe.fragrance_amount > 0 or (hasattr(recipe, 'modifiers') and recipe.modifiers)
print(f"   has_additives: {has_additives}")
print(f"   hasattr(recipe, 'modifiers'): {hasattr(recipe, 'modifiers')}")
print(f"   recipe.modifiers: {recipe.modifiers}")
print(f"   bool(recipe.modifiers): {bool(recipe.modifiers)}")

if hasattr(recipe, 'modifiers') and recipe.modifiers:
    print("\n   Modifiers would appear in PDF:")
    for modifier_name, amount_grams in recipe.modifiers.items():
        modifier_info = chemistry.get_modifier_info(modifier_name)
        if modifier_info:
            print(f"   - {modifier_name}: {amount_grams}g")
        else:
            print(f"   - {modifier_name}: ERROR - info not found!")
else:
    print("\n   ERROR: Modifiers would NOT appear in PDF!")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
