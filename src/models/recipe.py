"""
Recipe manager for saving, loading, and managing soap recipes.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class Recipe:
    """Represents a soap recipe with all its components."""
    
    def __init__(self, name: str, oils: Dict[str, float], 
                 superfat: float = 5.0, lye_concentration: float = 33.0,
                 fragrance_percent: float = 3.0, notes: str = "",
                 modifiers: Dict[str, float] = None):
        self.name = name
        self.oils = oils  # {oil_name: weight_in_grams}
        self.superfat = superfat
        self.lye_concentration = lye_concentration
        self.fragrance_percent = fragrance_percent
        self.notes = notes
        self.modifiers = modifiers if modifiers is not None else {}  # {modifier_name: amount}
        self.created_date = datetime.now().isoformat()
        self.modified_date = self.created_date
        
        # Calculated values (to be filled by chemistry calculator)
        self.lye_amount = 0.0
        self.water_amount = 0.0
        self.fragrance_amount = 0.0
        self.lye_adjustment = 0.0  # Extra lye needed for citric acid
        self.properties = {}
        self.fatty_acids = {}
    
    def to_dict(self) -> Dict:
        """Convert recipe to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'oils': self.oils,
            'superfat': self.superfat,
            'lye_concentration': self.lye_concentration,
            'fragrance_percent': self.fragrance_percent,
            'notes': self.notes,
            'modifiers': self.modifiers,
            'created_date': self.created_date,
            'modified_date': self.modified_date,
            'lye_amount': self.lye_amount,
            'water_amount': self.water_amount,
            'fragrance_amount': self.fragrance_amount,
            'lye_adjustment': self.lye_adjustment,
            'properties': self.properties,
            'fatty_acids': self.fatty_acids
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Recipe':
        """Create recipe from dictionary."""
        recipe = cls(
            name=data['name'],
            oils=data['oils'],
            superfat=data.get('superfat', 5.0),
            lye_concentration=data.get('lye_concentration', 33.0),
            fragrance_percent=data.get('fragrance_percent', 3.0),
            notes=data.get('notes', ''),
            modifiers=data.get('modifiers', {})
        )
        recipe.created_date = data.get('created_date', recipe.created_date)
        recipe.modified_date = data.get('modified_date', recipe.modified_date)
        recipe.lye_amount = data.get('lye_amount', 0.0)
        recipe.water_amount = data.get('water_amount', 0.0)
        recipe.fragrance_amount = data.get('fragrance_amount', 0.0)
        recipe.lye_adjustment = data.get('lye_adjustment', 0.0)
        recipe.properties = data.get('properties', {})
        recipe.fatty_acids = data.get('fatty_acids', {})
        return recipe


class RecipeManager:
    """Manages recipe storage and retrieval."""
    
    def __init__(self, recipes_file: str):
        self.recipes_file = recipes_file
        self.recipes: List[Recipe] = []
        self.load_recipes()
    
    def load_recipes(self):
        """Load recipes from JSON file."""
        if os.path.exists(self.recipes_file):
            try:
                with open(self.recipes_file, 'r') as f:
                    data = json.load(f)
                    self.recipes = [Recipe.from_dict(r) for r in data.get('recipes', [])]
            except Exception as e:
                print(f"Error loading recipes: {e}")
                self.recipes = []
        else:
            self.recipes = []
    
    def save_recipes(self):
        """Save all recipes to JSON file."""
        try:
            data = {'recipes': [r.to_dict() for r in self.recipes]}
            with open(self.recipes_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving recipes: {e}")
    
    def add_recipe(self, recipe: Recipe):
        """Add a new recipe."""
        self.recipes.append(recipe)
        self.save_recipes()
    
    def update_recipe(self, index: int, recipe: Recipe):
        """Update an existing recipe."""
        if 0 <= index < len(self.recipes):
            recipe.modified_date = datetime.now().isoformat()
            self.recipes[index] = recipe
            self.save_recipes()
    
    def delete_recipe(self, index: int):
        """Delete a recipe."""
        if 0 <= index < len(self.recipes):
            self.recipes.pop(index)
            self.save_recipes()
    
    def get_recipe(self, index: int) -> Optional[Recipe]:
        """Get a recipe by index."""
        if 0 <= index < len(self.recipes):
            return self.recipes[index]
        return None
    
    def get_all_recipes(self) -> List[Recipe]:
        """Get all recipes."""
        return self.recipes
    
    def search_recipes(self, search_term: str) -> List[Recipe]:
        """Search recipes by name or notes."""
        search_term = search_term.lower()
        return [r for r in self.recipes 
                if search_term in r.name.lower() or search_term in r.notes.lower()]
