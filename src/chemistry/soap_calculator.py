"""
Chemistry calculator module for soap making calculations.
Handles saponification values, lye calculations, and soap property predictions.
"""

import json
from typing import Dict, List, Tuple


class SoapChemistry:
    """Handles all chemistry-related calculations for soap making."""
    
    def __init__(self, oils_database_path: str, modifiers_database_path: str = None):
        """Initialize with oils database."""
        with open(oils_database_path, 'r') as f:
            data = json.load(f)
            self.oils_db = {oil['name']: oil for oil in data['oils']}
        
        # Load modifiers database if provided
        self.modifiers_db = {}
        if modifiers_database_path:
            try:
                with open(modifiers_database_path, 'r') as f:
                    data = json.load(f)
                    self.modifiers_db = {mod['name']: mod for mod in data['modifiers']}
            except Exception as e:
                print(f"Could not load modifiers database: {e}")
    
    def calculate_lye_amount(self, oil_weights: Dict[str, float], 
                            superfat_percent: float = 5.0,
                            modifiers: Dict[str, float] = None,
                            lye_type: str = 'NaOH') -> Tuple[float, float]:
        """
        Calculate required lye amount for saponification.
        
        Args:
            oil_weights: Dictionary of {oil_name: weight_in_grams}
            superfat_percent: Percentage of oils left unsaponified (default 5%)
            modifiers: Dictionary of {modifier_name: amount_in_grams}
            lye_type: 'NaOH' for sodium hydroxide or 'KOH' for potassium hydroxide
            
        Returns:
            Tuple of (required lye weight in grams, lye adjustment for modifiers)
        """
        total_lye = 0.0
        sap_key = 'sap_naoh' if lye_type == 'NaOH' else 'sap_koh'
        
        for oil_name, weight in oil_weights.items():
            if oil_name not in self.oils_db:
                raise ValueError(f"Oil '{oil_name}' not found in database")
            
            sap_value = self.oils_db[oil_name][sap_key]
            total_lye += weight * sap_value
        
        # Apply superfat reduction
        total_lye *= (1 - superfat_percent / 100)
        
        # Calculate lye adjustment for modifiers (e.g., citric acid)
        lye_adjustment = 0.0
        if modifiers:
            for modifier_name, amount in modifiers.items():
                if modifier_name in self.modifiers_db:
                    modifier = self.modifiers_db[modifier_name]
                    if 'lye_adjustment_factor' in modifier:
                        # citric acid: 0.6g NaOH per 1g citric acid
                        lye_adjustment += amount * modifier['lye_adjustment_factor']
        
        return round(total_lye, 2), round(lye_adjustment, 2)
    
    def calculate_water_amount(self, lye_weight: float, 
                               lye_concentration: float = 33.0) -> float:
        """
        Calculate water amount based on lye concentration.
        
        Args:
            lye_weight: Weight of lye in grams
            lye_concentration: Percentage of lye in water solution (default 33%)
            
        Returns:
            Required water weight in grams
        """
        # lye_concentration = lye / (lye + water) * 100
        # water = lye * (100 - lye_concentration) / lye_concentration
        water = lye_weight * (100 - lye_concentration) / lye_concentration
        return round(water, 2)
    
    def calculate_soap_properties(self, oil_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate predicted soap properties based on oil composition.
        
        Args:
            oil_weights: Dictionary of {oil_name: weight_in_grams}
            
        Returns:
            Dictionary of soap properties with their values
        """
        total_weight = sum(oil_weights.values())
        if total_weight == 0:
            return {}
        
        # Initialize property accumulators
        properties = {
            'hardness': 0.0,
            'cleansing': 0.0,
            'conditioning': 0.0,
            'bubbly': 0.0,
            'creamy': 0.0,
            'iodine': 0.0,
            'ins': 0.0
        }
        
        # Calculate weighted average of each property
        for oil_name, weight in oil_weights.items():
            if oil_name not in self.oils_db:
                continue
            
            percentage = weight / total_weight
            oil_props = self.oils_db[oil_name]['properties']
            
            for prop in properties:
                properties[prop] += oil_props[prop] * percentage
        
        # Round values
        return {k: round(v, 1) for k, v in properties.items()}
    
    def calculate_fatty_acid_profile(self, oil_weights: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate fatty acid composition of the soap.
        
        Args:
            oil_weights: Dictionary of {oil_name: weight_in_grams}
            
        Returns:
            Dictionary of fatty acid percentages
        """
        total_weight = sum(oil_weights.values())
        if total_weight == 0:
            return {}
        
        fatty_acids = {
            'lauric': 0.0,
            'myristic': 0.0,
            'palmitic': 0.0,
            'stearic': 0.0,
            'ricinoleic': 0.0,
            'oleic': 0.0,
            'linoleic': 0.0,
            'linolenic': 0.0
        }
        
        for oil_name, weight in oil_weights.items():
            if oil_name not in self.oils_db:
                continue
            
            percentage = weight / total_weight
            oil_fa = self.oils_db[oil_name]['fatty_acids']
            
            for fa in fatty_acids:
                fatty_acids[fa] += oil_fa[fa] * percentage
        
        return {k: round(v, 1) for k, v in fatty_acids.items()}
    
    def calculate_fragrance_amount(self, total_oil_weight: float, 
                                   fragrance_percent: float = 3.0) -> float:
        """
        Calculate fragrance/essential oil amount.
        
        Args:
            total_oil_weight: Total weight of oils in grams
            fragrance_percent: Percentage of fragrance to add (default 3%)
            
        Returns:
            Fragrance weight in grams
        """
        return round(total_oil_weight * fragrance_percent / 100, 2)
    
    def get_available_oils(self) -> List[str]:
        """Get list of all available oils in database."""
        return sorted(self.oils_db.keys())
    
    def get_oil_info(self, oil_name: str) -> Dict:
        """Get detailed information about a specific oil."""
        return self.oils_db.get(oil_name, {})
    
    def get_available_modifiers(self) -> List[str]:
        """Get list of all available modifiers."""
        return sorted(self.modifiers_db.keys())
    
    def get_modifier_info(self, modifier_name: str) -> Dict:
        """Get detailed information about a specific modifier."""
        return self.modifiers_db.get(modifier_name, {})
    
    def calculate_modifier_amount(self, modifier_name: str, 
                                  total_oil_weight: float,
                                  usage_percent: float = None) -> float:
        """
        Calculate recommended amount for a modifier.
        
        Args:
            modifier_name: Name of the modifier
            total_oil_weight: Total weight of oils in grams
            usage_percent: Custom usage percentage (uses typical if not provided)
            
        Returns:
            Modifier amount in grams
        """
        if modifier_name not in self.modifiers_db:
            return 0.0
        
        modifier = self.modifiers_db[modifier_name]
        
        if usage_percent is None:
            usage_percent = modifier.get('typical_usage_percent', 1.0)
        
        # Calculate based on usage rate type
        usage_type = modifier.get('usage_rate_type', 'percent_of_oils')
        
        if usage_type == 'percent_of_oils':
            return round(total_oil_weight * usage_percent / 100, 2)
        else:
            # For other types (tablespoons, etc.), return the percentage value
            # The user will need to interpret this
            return usage_percent
    
    def apply_modifier_effects(self, base_properties: Dict[str, float], 
                               modifiers: Dict[str, float]) -> Dict[str, float]:
        """
        Apply modifier effects to soap properties.
        
        Args:
            base_properties: Base properties calculated from oils
            modifiers: Dictionary of {modifier_name: amount_in_grams}
            
        Returns:
            Adjusted properties dictionary
        """
        adjusted_props = base_properties.copy()
        
        # Define modifier effects on properties (using actual modifier names)
        modifier_effects = {
            'Sugar': {'bubbly': 3, 'conditioning': 1},
            'Honey': {'bubbly': 2, 'conditioning': 2, 'creamy': 1},
            'Silk Amino Acids': {'creamy': 3, 'conditioning': 2},
            'Sodium Lactate': {'hardness': 2},
            'Citric Acid': {'hardness': 1, 'conditioning': 1},
            'Colloidal Oatmeal': {'conditioning': 2},
            'Tussah Silk Fibers': {'creamy': 2},
            'Kaolin Clay': {'creamy': 1, 'hardness': 1},
            'Bentonite Clay': {'creamy': 2},
            'Vitamin E Oil': {'conditioning': 1}
        }
        
        for modifier_name, amount in modifiers.items():
            if modifier_name in modifier_effects and amount > 0:
                effects = modifier_effects[modifier_name]
                for prop, boost in effects.items():
                    if prop in adjusted_props:
                        adjusted_props[prop] = round(adjusted_props[prop] + boost, 1)
        
        return adjusted_props

