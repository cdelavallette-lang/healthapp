"""
Nutrient Synergy Analyzer for Meal Planning

This module analyzes meals for:
1. Nutrient synergies (combinations that work better together)
2. Nutrient antagonists (combinations that interfere with each other)
3. Missing components to complete beneficial synergies
4. Timing recommendations for optimal absorption
"""

import json
from typing import Dict, List
from pathlib import Path


class SynergyAnalyzer:
    """Analyze nutrient synergies and antagonisms in meals."""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize analyzer with nutrient interactions data.
        
        Args:
            data_dir: Path to data directory. Defaults to ../data from this file.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        else:
            data_dir = Path(data_dir)
        
        # Load nutrient interactions
        interactions_path = data_dir / "nutrition-requirements" / "nutrient-interactions.json"
        with open(interactions_path, 'r') as f:
            self.interactions = json.load(f)
        
        self.synergies = self.interactions.get('nutrientSynergies', {})
        self.food_combinations = self.interactions.get('foodCombinations', {})
    
    def analyze_meal_synergies(self, meal_nutrients: Dict, meal_ingredients: List[str]) -> Dict:
        """
        Analyze a meal for nutrient synergies and antagonisms.
        
        Args:
            meal_nutrients: Calculated nutrient totals for the meal
            meal_ingredients: List of food IDs in the meal
            
        Returns:
            Analysis with detected synergies, missing components, and warnings
        """
        analysis = {
            'detected_synergies': [],
            'incomplete_synergies': [],
            'antagonistic_combinations': [],
            'timing_recommendations': [],
            'overall_score': 0
        }
        
        # Check each defined synergy
        for synergy in self.synergies:
            synergy_name = synergy.get('name', '')
            required_nutrients = synergy.get('nutrients', [])
            result = self._check_synergy(synergy, meal_nutrients)
            
            if result['complete']:
                analysis['detected_synergies'].append({
                    'name': synergy_name,
                    'benefit': synergy.get('benefit', ''),
                    'mechanism': synergy.get('mechanism', ''),
                    'present_nutrients': result['present']
                })
            elif result['partial']:
                analysis['incomplete_synergies'].append({
                    'name': synergy_name,
                    'benefit': synergy.get('benefit', ''),
                    'present_nutrients': result['present'],
                    'missing_nutrients': result['missing'],
                    'suggestions': self._get_food_suggestions(result['missing'])
                })
        
        # Check for antagonistic combinations
        antagonisms = self._check_antagonisms(meal_nutrients)
        analysis['antagonistic_combinations'] = antagonisms
        
        # Add timing recommendations
        timing_recs = self._get_timing_recommendations(meal_nutrients, meal_ingredients)
        analysis['timing_recommendations'] = timing_recs
        
        # Calculate overall synergy score (0-100)
        complete_synergies = len(analysis['detected_synergies'])
        total_possible = len(self.synergies)
        antagonism_penalty = len(antagonisms) * 5
        analysis['overall_score'] = max(0, min(100, (complete_synergies / total_possible * 100) - antagonism_penalty))
        
        return analysis
    
    def analyze_daily_meal_timing(self, daily_meals: Dict) -> List[Dict]:
        """
        Analyze timing of all meals throughout the day for optimal nutrient absorption.
        
        Args:
            daily_meals: Dict with breakfast, lunch, dinner, snacks
            
        Returns:
            List of timing recommendations and warnings
        """
        recommendations = []
        
        # Check if iron-rich meals are separated from calcium-rich meals
        iron_meals = []
        calcium_meals = []
        
        for meal_time, meal in daily_meals.items():
            if not meal:
                continue
            nutrients = meal.get('nutrients', {})
            iron = nutrients.get('minerals', {}).get('iron_mg', 0)
            calcium = nutrients.get('minerals', {}).get('calcium_mg', 0)
            
            if iron > 5:  # Significant iron
                iron_meals.append(meal_time)
            if calcium > 300:  # Significant calcium
                calcium_meals.append(meal_time)
        
        # Check for overlap
        overlap = set(iron_meals) & set(calcium_meals)
        if overlap:
            recommendations.append({
                'type': 'warning',
                'severity': 'medium',
                'message': f"High calcium and iron in same meal ({', '.join(overlap)}). Calcium can reduce iron absorption by up to 50%.",
                'suggestion': "Consider separating iron-rich and calcium-rich foods by 2-3 hours for optimal absorption."
            })
        
        return recommendations
    
    def get_synergy_completion_suggestions(self, meal_nutrients: Dict) -> List[Dict]:
        """
        Suggest foods to add to complete beneficial synergies.
        
        Args:
            meal_nutrients: Current meal nutrient totals
            
        Returns:
            List of suggestions with specific foods to add
        """
        suggestions = []
        
        # Check bone health synergy (most important)
        has_calcium = meal_nutrients.get('minerals', {}).get('calcium_mg', 0) > 200
        has_vitamin_d = meal_nutrients.get('vitamins', {}).get('vitaminD_IU', 0) > 200
        has_vitamin_k2 = meal_nutrients.get('vitamins', {}).get('vitaminK2_mcg', 0) > 10
        has_magnesium = meal_nutrients.get('minerals', {}).get('magnesium_mg', 0) > 50
        
        if has_calcium:
            missing = []
            if not has_vitamin_d:
                missing.append("Vitamin D")
            if not has_vitamin_k2:
                missing.append("Vitamin K2")
            if not has_magnesium:
                missing.append("Magnesium")
            
            if missing:
                suggestions.append({
                    'synergy': 'Bone Health Trio',
                    'missing': missing,
                    'benefit': 'Ensures calcium goes to bones, not arteries (50% reduction in cardiovascular mortality with K2)',
                    'food_suggestions': self._get_bone_health_foods(missing)
                })
        
        # Check iron absorption complex
        has_iron = meal_nutrients.get('minerals', {}).get('iron_mg', 0) > 3
        has_vitamin_c = meal_nutrients.get('vitamins', {}).get('vitaminC_mg', 0) > 25
        
        if has_iron and not has_vitamin_c:
            suggestions.append({
                'synergy': 'Iron Absorption Complex',
                'missing': ['Vitamin C'],
                'benefit': 'Increases iron absorption by 3x (critical for plant-based iron)',
                'food_suggestions': [
                    'Add 1/2 red bell pepper (95mg vitamin C)',
                    'Include 1/2 cup berries (40mg vitamin C)',
                    'Add lemon juice to meal (20mg vitamin C)'
                ]
            })
        
        return suggestions
    
    # Helper methods
    
    def _check_synergy(self, synergy: Dict, nutrients: Dict) -> Dict:
        """Check if a synergy is complete, partial, or missing."""
        required = synergy.get('nutrients', [])
        present = []
        missing = []
        
        for nutrient in required:
            if self._has_nutrient(nutrient, nutrients):
                present.append(nutrient)
            else:
                missing.append(nutrient)
        
        return {
            'complete': len(missing) == 0,
            'partial': len(present) > 0 and len(missing) > 0,
            'present': present,
            'missing': missing
        }
    
    def _has_nutrient(self, nutrient_name: str, nutrients: Dict, threshold_percent: float = 0.15) -> bool:
        """
        Check if meal contains significant amount of a nutrient.
        
        Args:
            nutrient_name: Name of nutrient (e.g., "calcium", "vitaminD")
            nutrients: Nutrient totals dict
            threshold_percent: Minimum % of daily needs to count as "present"
        """
        # Map nutrient names to keys and thresholds
        nutrient_thresholds = {
            'calcium': ('minerals', 'calcium_mg', 150),  # 15% of 1000mg
            'vitaminD': ('vitamins', 'vitaminD_IU', 400),  # 15% of 2500 IU
            'vitaminK2': ('vitamins', 'vitaminK2_mcg', 15),  # 15% of 100mcg
            'magnesium': ('minerals', 'magnesium_mg', 60),  # 15% of 400mg
            'iron': ('minerals', 'iron_mg', 2),  # 15% of 15mg
            'vitaminC': ('vitamins', 'vitaminC_mg', 25),  # 15% of 150mg
            'zinc': ('minerals', 'zinc_mg', 1.5),  # 15% of 10mg
            'copper': ('minerals', 'copper_mg', 0.15),  # 15% of 1mg
            'vitaminE': ('vitamins', 'vitaminE_mg', 3),  # 15% of 20mg
            'vitaminA': ('vitamins', 'vitaminA_mcg', 150),  # 15% of 1000mcg
            'selenium': ('minerals', 'selenium_mcg', 30),  # 15% of 200mcg
        }
        
        if nutrient_name not in nutrient_thresholds:
            return False
        
        category, key, threshold = nutrient_thresholds[nutrient_name]
        value = nutrients.get(category, {}).get(key, 0)
        
        return value >= threshold
    
    def _check_antagonisms(self, nutrients: Dict) -> List[Dict]:
        """Check for nutrient antagonisms (combinations that interfere with absorption)."""
        antagonisms = []
        
        calcium = nutrients.get('minerals', {}).get('calcium_mg', 0)
        iron = nutrients.get('minerals', {}).get('iron_mg', 0)
        zinc = nutrients.get('minerals', {}).get('zinc_mg', 0)
        copper = nutrients.get('minerals', {}).get('copper_mg', 0)
        
        # Calcium + Iron antagonism
        if calcium > 300 and iron > 5:
            antagonisms.append({
                'type': 'Calcium-Iron Competition',
                'severity': 'high',
                'description': f'High calcium ({calcium}mg) and iron ({iron}mg) in same meal',
                'impact': 'Calcium can reduce iron absorption by 30-50%',
                'recommendation': 'Separate high-calcium and high-iron meals by 2+ hours'
            })
        
        # Zinc-Copper ratio
        if zinc > 5 and copper > 0:
            ratio = zinc / copper if copper > 0 else 999
            if ratio > 15:
                antagonisms.append({
                    'type': 'Zinc-Copper Imbalance',
                    'severity': 'medium',
                    'description': f'Zinc:Copper ratio is {ratio:.1f}:1 (optimal is 10:1)',
                    'impact': 'Excess zinc can deplete copper stores over time',
                    'recommendation': 'Add copper-rich foods (liver, shellfish, nuts) or reduce zinc supplementation'
                })
        
        # Fiber + Fat-soluble vitamins
        fiber = nutrients.get('macronutrients', {}).get('fiber_g', 0)
        fat_sol_vitamins = (nutrients.get('vitamins', {}).get('vitaminA_mcg', 0) + 
                           nutrients.get('vitamins', {}).get('vitaminD_IU', 0) / 40 +
                           nutrients.get('vitamins', {}).get('vitaminE_mg', 0) +
                           nutrients.get('vitamins', {}).get('vitaminK_mcg', 0) / 10)
        
        if fiber > 15 and fat_sol_vitamins > 100:
            antagonisms.append({
                'type': 'High Fiber + Fat-Soluble Vitamins',
                'severity': 'low',
                'description': f'Very high fiber ({fiber}g) may reduce absorption of fat-soluble vitamins',
                'impact': 'Fiber can bind to vitamins A, D, E, K and reduce absorption',
                'recommendation': 'Ensure adequate healthy fats in meal to offset fiber binding'
            })
        
        return antagonisms
    
    def _get_timing_recommendations(self, nutrients: Dict, ingredients: List[str]) -> List[str]:
        """Get timing recommendations based on circadian nutrition principles."""
        recommendations = []
        
        protein = nutrients.get('macronutrients', {}).get('protein_g', 0)
        carbs = nutrients.get('macronutrients', {}).get('carbohydrates_g', 0)
        magnesium = nutrients.get('minerals', {}).get('magnesium_mg', 0)
        
        if protein > 30:
            recommendations.append("✓ High protein content - ideal for morning or post-workout to maximize muscle protein synthesis")
        
        if carbs > 50 and 'sweet_potato' in ' '.join(ingredients):
            recommendations.append("✓ Complex carbohydrates present - consuming in evening can improve sleep quality (increases serotonin)")
        
        if magnesium > 100:
            recommendations.append("✓ High magnesium - best consumed in evening for relaxation and sleep support")
        
        # Check for tea/coffee with iron-rich meal
        has_iron = nutrients.get('minerals', {}).get('iron_mg', 0) > 5
        if has_iron:
            recommendations.append("⚠️ Iron-rich meal - avoid tea/coffee for 1-2 hours before and after (tannins reduce iron absorption by 60-70%)")
        
        return recommendations
    
    def _get_food_suggestions(self, missing_nutrients: List[str]) -> List[str]:
        """Get food suggestions for missing nutrients."""
        food_map = {
            'calcium': ['Grass-fed yogurt (300mg per cup)', 'Sardines with bones (350mg per 100g)', 'Kale (150mg per cup)'],
            'vitaminD': ['Wild salmon (600 IU per 100g)', 'Pastured egg yolks (50 IU per yolk)', 'UV-exposed mushrooms (400 IU per 100g)'],
            'vitaminK2': ['Grass-fed cheese (50mcg per oz)', 'Natto (850mcg per 100g)', 'Pastured egg yolks (15mcg per yolk)'],
            'magnesium': ['Pumpkin seeds (150mg per oz)', 'Spinach (157mg per cup cooked)', 'Dark chocolate (95mg per oz)'],
            'iron': ['Grass-fed beef (3mg per 100g)', 'Liver (6mg per 100g)', 'Lentils with vitamin C (3mg per cup)'],
            'vitaminC': ['Red bell pepper (190mg per pepper)', 'Strawberries (90mg per cup)', 'Broccoli (80mg per cup)'],
            'zinc': ['Oysters (78mg per 100g)', 'Grass-fed beef (7mg per 100g)', 'Pumpkin seeds (10mg per oz)'],
            'copper': ['Beef liver (14mg per 100g)', 'Oysters (7mg per 100g)', 'Cashews (2mg per oz)']
        }
        
        suggestions = []
        for nutrient in missing_nutrients:
            if nutrient in food_map:
                suggestions.extend(food_map[nutrient])
        
        return suggestions
    
    def _get_bone_health_foods(self, missing_nutrients: List[str]) -> List[str]:
        """Get specific bone health food suggestions."""
        suggestions = []
        
        if 'Vitamin D' in missing_nutrients:
            suggestions.append('Add 100g wild salmon (+600 IU vitamin D)')
        if 'Vitamin K2' in missing_nutrients:
            suggestions.append('Add 1oz grass-fed cheese (+50mcg vitamin K2)')
        if 'Magnesium' in missing_nutrients:
            suggestions.append('Add 1oz pumpkin seeds (+150mg magnesium)')
        
        return suggestions


if __name__ == "__main__":
    # Example usage
    analyzer = SynergyAnalyzer()
    
    # Example meal nutrients
    example_meal = {
        'minerals': {
            'calcium_mg': 400,
            'iron_mg': 6,
            'magnesium_mg': 80,
            'zinc_mg': 5,
            'copper_mg': 0.3
        },
        'vitamins': {
            'vitaminD_IU': 500,
            'vitaminK2_mcg': 5,  # Missing for complete bone synergy
            'vitaminC_mg': 60
        },
        'macronutrients': {
            'protein_g': 35,
            'fiber_g': 8
        }
    }
    
    example_ingredients = ['salmon', 'spinach', 'quinoa']
    
    analysis = analyzer.analyze_meal_synergies(example_meal, example_ingredients)
    print(json.dumps(analysis, indent=2))
