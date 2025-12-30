"""
Nutrient Calculator for Family Meal Planning Application

This module provides functionality to:
1. Calculate total nutrients from meal plans
2. Compare against optimal nutritional requirements
3. Identify nutrient gaps and excesses
4. Generate recommendations for balancing meal plans
"""

import json
from typing import Dict, List, Tuple
from pathlib import Path


class NutrientCalculator:
    """Calculate and analyze nutrients from meal plans."""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize calculator with nutrition requirements and food database.
        
        Args:
            data_dir: Path to data directory. Defaults to ../data from this file.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        else:
            data_dir = Path(data_dir)
            
        self.data_dir = data_dir
        
        # Load nutrition requirements
        req_path = data_dir / "nutrition-requirements" / "optimal-nutrients-adult.json"
        with open(req_path, 'r') as f:
            self.requirements = json.load(f)
            
        # Load food database
        food_path = data_dir / "foods" / "whole-foods-database.json"
        with open(food_path, 'r') as f:
            self.food_db = json.load(f)
            
        # Load nutrient interactions for bioavailability
        interactions_path = data_dir / "nutrition-requirements" / "nutrient-interactions.json"
        try:
            with open(interactions_path, 'r') as f:
                self.nutrient_interactions = json.load(f)
        except FileNotFoundError:
            print("Warning: nutrient-interactions.json not found. Bioavailability tracking disabled.")
            self.nutrient_interactions = None
    
    def calculate_meal_nutrients(self, ingredients: List[Dict], apply_bioavailability: bool = True) -> Dict:
        """
        Calculate total nutrients from a list of ingredients.
        
        Args:
            ingredients: List of ingredient dicts with foodId, amount, unit
            apply_bioavailability: Whether to apply bioavailability adjustments
            
        Returns:
            Dictionary with aggregated nutrients (raw and bioavailable)
        """
        totals = self._init_nutrient_totals()
        
        # Track food sources for bioavailability calculations
        food_sources = {
            'animal_foods': [],
            'plant_foods': [],
            'has_vitamin_c': False,
            'has_fat': False
        }
        
        for ingredient in ingredients:
            food_id = ingredient.get('foodId')
            amount = ingredient.get('amount', 0)
            unit = ingredient.get('unit', 'g')
            
            # Find food in database
            food = self._find_food(food_id)
            if not food:
                print(f"Warning: Food {food_id} not found in database")
                continue
            
            # Track food source type for bioavailability
            food_type = self._get_food_type(food_id)
            if food_type == 'animal':
                food_sources['animal_foods'].append(food_id)
            else:
                food_sources['plant_foods'].append(food_id)
            
            # Convert to grams if needed
            amount_g = self._convert_to_grams(amount, unit)
            
            # Get nutrients and scale to amount
            nutrients = food.get('nutrients', {})
            serving_size = self._parse_serving_size(food.get('serving_size', '100g'))
            scaling_factor = amount_g / serving_size
            
            # Check for vitamin C and fat (important for bioavailability)
            if nutrients.get('vitaminC_mg', 0) * scaling_factor > 25:
                food_sources['has_vitamin_c'] = True
            if nutrients.get('fat_g', 0) * scaling_factor > 5:
                food_sources['has_fat'] = True
            
            # Add scaled nutrients to totals
            self._add_scaled_nutrients(totals, nutrients, scaling_factor)
        
        # Apply bioavailability adjustments if enabled
        if apply_bioavailability and self.nutrient_interactions:
            totals = self._apply_bioavailability(totals, food_sources)
        
        return totals
    
    def calculate_daily_nutrients(self, daily_meals: Dict) -> Dict:
        """
        Calculate total nutrients for a day of meals.
        
        Args:
            daily_meals: Dict with breakfast, lunch, dinner, snacks
            
        Returns:
            Dictionary with total daily nutrients
        """
        daily_totals = self._init_nutrient_totals()
        
        # Process main meals
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            if meal_type in daily_meals:
                meal = daily_meals[meal_type]
                ingredients = meal.get('ingredients', [])
                meal_nutrients = self.calculate_meal_nutrients(ingredients)
                self._add_nutrients(daily_totals, meal_nutrients)
        
        # Process snacks
        if 'snacks' in daily_meals:
            for snack in daily_meals['snacks']:
                ingredients = snack.get('ingredients', [])
                snack_nutrients = self.calculate_meal_nutrients(ingredients)
                self._add_nutrients(daily_totals, snack_nutrients)
        
        return daily_totals
    
    def calculate_weekly_nutrients(self, weekly_plan: Dict) -> Tuple[Dict, Dict]:
        """
        Calculate nutrients for entire week.
        
        Args:
            weekly_plan: Dict with monday-sunday meal plans
            
        Returns:
            Tuple of (weekly_totals, daily_averages)
        """
        weekly_totals = self._init_nutrient_totals()
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            if day in weekly_plan:
                daily_nutrients = self.calculate_daily_nutrients(weekly_plan[day])
                self._add_nutrients(weekly_totals, daily_nutrients)
        
        # Calculate daily averages
        daily_averages = self._divide_nutrients(weekly_totals, 7)
        
        return weekly_totals, daily_averages
    
    def analyze_nutrient_compliance(self, daily_nutrients: Dict, demographic: str = "25-50") -> Dict:
        """
        Compare daily nutrients against optimal requirements.
        
        Args:
            daily_nutrients: Calculated daily nutrient totals
            demographic: Age range for requirements (default "25-50")
            
        Returns:
            Analysis with compliance percentage and gaps
        """
        analysis = {
            'compliantNutrients': [],
            'deficientNutrients': [],
            'excessiveNutrients': [],
            'compliancePercentage': 0
        }
        
        # Extract macronutrients from requirements
        macros = self.requirements.get('macronutrients', {})
        vitamins = self.requirements.get('vitamins', {})
        minerals = self.requirements.get('minerals', {})
        other = self.requirements.get('other_nutrients', {})
        
        total_checked = 0
        compliant_count = 0
        
        # Check macronutrients
        macro_map = {
            'protein_g': ('protein', 'optimal_g'),
            'carbohydrates_g': ('carbohydrates', 'optimal_g'),
            'fat_g': ('fats', 'optimal_g'),
            'fiber_g': ('fiber', 'optimal_g')
        }
        
        for nutrient_key, (req_key, value_key) in macro_map.items():
            if req_key in macros:
                is_compliant, status = self._check_nutrient(
                    daily_nutrients['macronutrients'].get(nutrient_key, 0),
                    macros[req_key],
                    nutrient_key
                )
                total_checked += 1
                if is_compliant:
                    compliant_count += 1
                    analysis['compliantNutrients'].append(status)
                elif status['percentOfTarget'] < 100:
                    analysis['deficientNutrients'].append(status)
                else:
                    analysis['excessiveNutrients'].append(status)
        
        # Check vitamins
        vitamin_map = {
            'vitaminA_mcg': ('vitaminA', 'optimal'),
            'vitaminD_IU': ('vitaminD', 'optimal'),
            'vitaminE_mg': ('vitaminE', 'optimal'),
            'vitaminC_mg': ('vitaminC', 'optimal'),
            'thiamin_B1_mg': ('thiamin_B1', 'optimal'),
            'riboflavin_B2_mg': ('riboflavin_B2', 'optimal'),
            'niacin_B3_mg': ('niacin_B3', 'optimal'),
            'pyridoxine_B6_mg': ('pyridoxine_B6', 'optimal'),
            'folate_B9_mcg': ('folate_B9', 'optimal'),
            'cobalamin_B12_mcg': ('cobalamin_B12', 'optimal')
        }
        
        for nutrient_key, (req_key, value_key) in vitamin_map.items():
            if req_key in vitamins:
                is_compliant, status = self._check_nutrient(
                    daily_nutrients['vitamins'].get(nutrient_key, 0),
                    vitamins[req_key],
                    nutrient_key
                )
                total_checked += 1
                if is_compliant:
                    compliant_count += 1
                    analysis['compliantNutrients'].append(status)
                elif status['percentOfTarget'] < 100:
                    analysis['deficientNutrients'].append(status)
                else:
                    analysis['excessiveNutrients'].append(status)
        
        # Check minerals
        mineral_map = {
            'calcium_mg': ('calcium', 'optimal'),
            'iron_mg': ('iron', 'optimal'),
            'magnesium_mg': ('magnesium', 'optimal'),
            'potassium_mg': ('potassium', 'optimal'),
            'zinc_mg': ('zinc', 'optimal'),
            'selenium_mcg': ('selenium', 'optimal')
        }
        
        for nutrient_key, (req_key, value_key) in mineral_map.items():
            if req_key in minerals:
                is_compliant, status = self._check_nutrient(
                    daily_nutrients['minerals'].get(nutrient_key, 0),
                    minerals[req_key],
                    nutrient_key
                )
                total_checked += 1
                if is_compliant:
                    compliant_count += 1
                    analysis['compliantNutrients'].append(status)
                elif status['percentOfTarget'] < 100:
                    analysis['deficientNutrients'].append(status)
                else:
                    analysis['excessiveNutrients'].append(status)
        
        # Check choline
        if 'choline' in other:
            is_compliant, status = self._check_nutrient(
                daily_nutrients['other'].get('choline_mg', 0),
                other['choline'],
                'choline_mg'
            )
            total_checked += 1
            if is_compliant:
                compliant_count += 1
                analysis['compliantNutrients'].append(status)
            elif status['percentOfTarget'] < 100:
                analysis['deficientNutrients'].append(status)
            else:
                analysis['excessiveNutrients'].append(status)
        
        # Calculate compliance percentage
        if total_checked > 0:
            analysis['compliancePercentage'] = round((compliant_count / total_checked) * 100, 1)
        
        return analysis
    
    def suggest_foods_for_deficiency(self, nutrient: str, amount_needed: float) -> List[Dict]:
        """
        Suggest foods that are high in a specific nutrient.
        
        Args:
            nutrient: Name of the deficient nutrient
            amount_needed: How much more is needed
            
        Returns:
            List of suggested foods with amounts
        """
        # This is a simplified version - could be much more sophisticated
        suggestions = []
        
        # Map nutrient keys to database keys
        nutrient_db_map = {
            'vitaminD_IU': 'vitaminD_IU',
            'vitaminB12_mcg': 'vitaminB12_mcg',
            'omega3_g': 'omega3_g',
            'choline_mg': 'choline_mg',
            'magnesium_mg': 'magnesium_mg',
            'iron_mg': 'iron_mg'
        }
        
        db_key = nutrient_db_map.get(nutrient, nutrient)
        
        # Search through food database for high sources
        # (This is simplified - would need more sophisticated ranking)
        
        return suggestions
    
    # Helper methods
    
    def _init_nutrient_totals(self) -> Dict:
        """Initialize empty nutrient totals dictionary."""
        return {
            'calories': 0,
            'macronutrients': {
                'protein_g': 0,
                'carbohydrates_g': 0,
                'fat_g': 0,
                'fiber_g': 0,
                'omega3_g': 0,
                'omega6_g': 0
            },
            'vitamins': {
                'vitaminA_mcg': 0,
                'vitaminA_mcg_bioavailable': 0,  # Track bioavailable separately
                'vitaminD_IU': 0,
                'vitaminE_mg': 0,
                'vitaminK_mcg': 0,
                'vitaminK2_mcg': 0,
                'vitaminC_mg': 0,
                'thiamin_B1_mg': 0,
                'riboflavin_B2_mg': 0,
                'niacin_B3_mg': 0,
                'pantothenicAcid_B5_mg': 0,
                'pyridoxine_B6_mg': 0,
                'biotin_B7_mcg': 0,
                'folate_B9_mcg': 0,
                'cobalamin_B12_mcg': 0
            },
            'minerals': {
                'calcium_mg': 0,
                'iron_mg': 0,
                'iron_mg_bioavailable': 0,  # Track absorbable iron
                'magnesium_mg': 0,
                'phosphorus_mg': 0,
                'potassium_mg': 0,
                'sodium_mg': 0,
                'zinc_mg': 0,
                'copper_mg': 0,
                'manganese_mg': 0,
                'selenium_mcg': 0,
                'iodine_mcg': 0,
                'chromium_mcg': 0,
                'molybdenum_mcg': 0
            },
            'other': {
                'choline_mg': 0,
                'water_ml': 0,
                'omega3_EPA_DHA_mg': 0,  # Track bioactive omega-3
                'omega3_ALA_mg': 0
            }
        }
    
    def _find_food(self, food_id: str) -> Dict:
        """Find food in database by ID."""
        # Search through all categories
        for category_name, category_data in self.food_db.get('categories', {}).items():
            for subcategory_name, foods in category_data.items():
                if isinstance(foods, list):
                    for food in foods:
                        if food.get('name', '').lower().replace(' ', '_') == food_id.lower():
                            return food
        return None
    
    def _parse_serving_size(self, serving_size: str) -> float:
        """Parse serving size string to grams."""
        # Simple parser - handles "100g", "1 large (50g)", etc.
        import re
        match = re.search(r'(\d+)g', serving_size)
        if match:
            return float(match.group(1))
        return 100.0  # default
    
    def _convert_to_grams(self, amount: float, unit: str) -> float:
        """Convert various units to grams."""
        # Simplified conversion - would need comprehensive conversion table
        conversions = {
            'g': 1,
            'oz': 28.35,
            'cup': 240,  # approximate, varies by ingredient
            'tbsp': 15,
            'tsp': 5,
            'ml': 1,
            'l': 1000
        }
        return amount * conversions.get(unit.lower(), 1)
    
    def _add_scaled_nutrients(self, totals: Dict, nutrients: Dict, scale: float):
        """Add scaled nutrients to totals."""
        for key, value in nutrients.items():
            if isinstance(value, (int, float)):
                # Determine which category this nutrient belongs to
                if key in totals['macronutrients']:
                    totals['macronutrients'][key] += value * scale
                elif key in totals['vitamins']:
                    totals['vitamins'][key] += value * scale
                elif key in totals['minerals']:
                    totals['minerals'][key] += value * scale
                elif key in totals['other']:
                    totals['other'][key] += value * scale
    
    def _add_nutrients(self, totals: Dict, nutrients: Dict):
        """Add nutrients from one dict to another."""
        totals['calories'] += nutrients.get('calories', 0)
        
        for category in ['macronutrients', 'vitamins', 'minerals', 'other']:
            if category in nutrients:
                for key, value in nutrients[category].items():
                    totals[category][key] += value
    
    def _divide_nutrients(self, nutrients: Dict, divisor: float) -> Dict:
        """Divide all nutrient values by a number (for averaging)."""
        result = self._init_nutrient_totals()
        result['calories'] = nutrients['calories'] / divisor
        
        for category in ['macronutrients', 'vitamins', 'minerals', 'other']:
            for key, value in nutrients[category].items():
                result[category][key] = round(value / divisor, 2)
        
        return result
    
    def _check_nutrient(self, actual: float, requirement: Dict, nutrient_name: str) -> Tuple[bool, Dict]:
        """
        Check if actual nutrient amount meets requirements.
        
        Returns:
            Tuple of (is_compliant, status_dict)
        """
        optimal = requirement.get('optimal', requirement.get('optimal_g', 0))
        min_val = requirement.get('min', requirement.get('min_g', optimal * 0.8))
        max_val = requirement.get('max', requirement.get('max_g', optimal * 1.5))
        
        percent_of_target = (actual / optimal * 100) if optimal > 0 else 0
        
        status = {
            'nutrient': nutrient_name,
            'actual': round(actual, 2),
            'optimal': optimal,
            'min': min_val,
            'max': max_val,
            'percentOfTarget': round(percent_of_target, 1),
            'status': 'optimal' if min_val <= actual <= max_val else ('deficient' if actual < min_val else 'excessive')
        }
        
        is_compliant = min_val <= actual <= max_val
        
        return is_compliant, status
    
    def _get_food_type(self, food_id: str) -> str:
        """Determine if food is animal or plant-based for bioavailability calculations."""
        animal_foods = ['salmon', 'sardines', 'eggs', 'beef', 'liver', 'chicken', 'turkey', 'oysters', 'shrimp']
        for animal in animal_foods:
            if animal in food_id.lower():
                return 'animal'
        return 'plant'
    
    def _apply_bioavailability(self, totals: Dict, food_sources: Dict) -> Dict:
        """
        Apply bioavailability adjustments based on nutrient interactions.
        
        Args:
            totals: Raw nutrient totals
            food_sources: Information about food types in meal
            
        Returns:
            Totals with bioavailability-adjusted values added
        """
        if not self.nutrient_interactions:
            return totals
        
        bio_factors = self.nutrient_interactions.get('bioavailabilityFactors', {})
        
        # Iron bioavailability
        if 'iron' in bio_factors:
            iron_total = totals['minerals']['iron_mg']
            has_animal = len(food_sources['animal_foods']) > 0
            has_vitamin_c = food_sources['has_vitamin_c']
            
            if has_animal:
                # Assume 50% of iron from animal sources (heme iron at 25% absorption)
                # and 50% from plant sources (non-heme at 10% with vitamin C boost)
                heme_iron = iron_total * 0.5
                nonheme_iron = iron_total * 0.5
                
                heme_absorbed = heme_iron * 0.25  # 25% absorption
                nonheme_rate = 0.15 if has_vitamin_c else 0.05  # 15% with vitamin C, 5% without
                nonheme_absorbed = nonheme_iron * nonheme_rate
                
                totals['minerals']['iron_mg_bioavailable'] = round(heme_absorbed + nonheme_absorbed, 2)
            else:
                # All plant iron (non-heme)
                absorption_rate = 0.15 if has_vitamin_c else 0.05
                totals['minerals']['iron_mg_bioavailable'] = round(iron_total * absorption_rate, 2)
        
        # Vitamin A bioavailability (retinol vs beta-carotene)
        if 'vitaminA' in bio_factors:
            vitamin_a_total = totals['vitamins']['vitaminA_mcg']
            has_animal = len(food_sources['animal_foods']) > 0
            has_fat = food_sources['has_fat']
            
            if has_animal:
                # Assume 50% from preformed retinol (100% bioavailable)
                # and 50% from beta-carotene (12:1 conversion)
                retinol = vitamin_a_total * 0.5
                beta_carotene = vitamin_a_total * 0.5
                
                beta_conversion = 0.083 if has_fat else 0.042  # 12:1 with fat, 24:1 without
                bioavailable = retinol + (beta_carotene * beta_conversion)
                
                totals['vitamins']['vitaminA_mcg_bioavailable'] = round(bioavailable, 2)
            else:
                # All beta-carotene from plants
                conversion_rate = 0.083 if has_fat else 0.042
                totals['vitamins']['vitaminA_mcg_bioavailable'] = round(vitamin_a_total * conversion_rate, 2)
        
        # Omega-3 bioavailability (EPA/DHA vs ALA)
        if 'omega3' in bio_factors:
            omega3_total = totals['macronutrients']['omega3_g']
            has_fish = any('salmon' in f or 'sardine' in f or 'mackerel' in f for f in food_sources['animal_foods'])
            
            if has_fish:
                # Fish provides direct EPA/DHA (assume 70% of omega-3 from fish is EPA+DHA)
                epa_dha_direct = omega3_total * 0.7 * 1000  # Convert to mg
                ala_remaining = omega3_total * 0.3 * 1000
                
                # ALA converts to EPA/DHA at 5% rate
                ala_converted = ala_remaining * 0.05
                
                totals['other']['omega3_EPA_DHA_mg'] = round(epa_dha_direct + ala_converted, 0)
                totals['other']['omega3_ALA_mg'] = round(ala_remaining, 0)
            else:
                # Plant sources only - all ALA with poor conversion
                ala_total = omega3_total * 1000
                ala_converted = ala_total * 0.05  # 5% conversion to EPA/DHA
                
                totals['other']['omega3_EPA_DHA_mg'] = round(ala_converted, 0)
                totals['other']['omega3_ALA_mg'] = round(ala_total, 0)
        
        return totals


if __name__ == "__main__":
    # Example usage
    calculator = NutrientCalculator()
    
    # Example meal
    example_meal = {
        'ingredients': [
            {'foodId': 'pasture_raised_eggs', 'amount': 150, 'unit': 'g'},  # 3 eggs
            {'foodId': 'wild_salmon', 'amount': 100, 'unit': 'g'},
            {'foodId': 'spinach', 'amount': 100, 'unit': 'g'}
        ]
    }
    
    nutrients = calculator.calculate_meal_nutrients(example_meal['ingredients'])
    print("Meal nutrients:", json.dumps(nutrients, indent=2))
