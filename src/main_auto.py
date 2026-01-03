"""
Auto Recipe Generator - Upgraded Soap Making Application
Select oils and specify batch size to automatically generate balanced recipes
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
from typing import Dict, List, Set
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chemistry.soap_calculator import SoapChemistry
from models.recipe import Recipe, RecipeManager


class AutoRecipeGenerator:
    """Generates balanced soap recipes based on selected oils and batch size."""
    
    # Predefined ratios for different oil combinations
    OIL_CATEGORIES = {
        'base': ['Olive Oil', 'Sunflower Oil', 'Sweet Almond Oil', 'Rice Bran Oil', 'Canola Oil', 
                 'Apricot Kernel Oil', 'Avocado Oil', 'Hazelnut Oil', 'Macadamia Nut Oil'],
        'hard': ['Coconut Oil', 'Palm Oil', 'Cocoa Butter', 'Shea Butter', 'Babassu Oil', 
                 'Beeswax', 'Mango Butter'],
        'super_fat': ['Castor Oil', 'Jojoba Oil'],
        'conditioning': ['Beef Tallow', 'Lard', 'Grapeseed Oil', 'Hemp Seed Oil', 'Safflower Oil'],
        'specialty': ['Argan Oil', 'Neem Oil']
    }
    
    @staticmethod
    def generate_recipe(selected_oils: List[str], total_weight_lbs: float, target_props: Dict = None) -> Dict[str, float]:
        """
        Generate a balanced recipe from selected oils, optionally targeting specific properties.
        
        Args:
            selected_oils: List of selected oil names
            total_weight_lbs: Total desired batch size in pounds
            target_props: Optional dictionary of target property values
            
        Returns:
            Dictionary of {oil_name: weight_in_oz}
        """
        if not selected_oils:
            return {}
        
        total_oz = total_weight_lbs * 16  # Convert pounds to ounces
        
        # If we have target properties, use intelligent allocation
        if target_props:
            return AutoRecipeGenerator.generate_targeted_recipe(selected_oils, total_oz, target_props)
        
        # Otherwise use default balanced approach
        # Categorize selected oils
        selected_base = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['base']]
        selected_hard = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['hard']]
        selected_super = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['super_fat']]
        selected_cond = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['conditioning']]
        selected_specialty = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['specialty']]
        
        recipe = {}
        
        # Strategy based on available oils
        if len(selected_oils) == 1:
            # Single oil - use 100%
            recipe[selected_oils[0]] = total_oz
            
        elif len(selected_oils) == 2:
            # Two oils - 70/30 split favoring base oils
            if selected_base and selected_hard:
                recipe[selected_base[0]] = total_oz * 0.70
                recipe[selected_hard[0]] = total_oz * 0.30
            else:
                recipe[selected_oils[0]] = total_oz * 0.60
                recipe[selected_oils[1]] = total_oz * 0.40
                
        elif len(selected_oils) == 3:
            # Three oils - balanced approach
            if selected_base and selected_hard:
                # Base + Hard + Other
                recipe[selected_base[0]] = total_oz * 0.50
                recipe[selected_hard[0]] = total_oz * 0.30
                other = [oil for oil in selected_oils if oil not in [selected_base[0], selected_hard[0]]][0]
                recipe[other] = total_oz * 0.20
            else:
                # Equal distribution
                for oil in selected_oils:
                    recipe[oil] = total_oz / 3
                    
        else:
            # Multiple oils - comprehensive recipe
            remaining_oz = total_oz
            
            # Allocate percentages
            # Base oils: 40-50%
            if selected_base:
                base_total = total_oz * 0.45
                per_base = base_total / len(selected_base)
                for oil in selected_base:
                    recipe[oil] = per_base
                remaining_oz -= base_total
            
            # Hard oils: 25-35%
            if selected_hard:
                hard_total = min(total_oz * 0.30, remaining_oz)
                per_hard = hard_total / len(selected_hard)
                for oil in selected_hard:
                    recipe[oil] = per_hard
                remaining_oz -= hard_total
            
            # Conditioning fats: 15-20%
            if selected_cond:
                cond_total = min(total_oz * 0.18, remaining_oz)
                per_cond = cond_total / len(selected_cond)
                for oil in selected_cond:
                    recipe[oil] = per_cond
                remaining_oz -= cond_total
            
            # Castor/Jojoba: 5-7%
            if selected_super:
                super_total = min(total_oz * 0.07, remaining_oz)
                per_super = super_total / len(selected_super)
                for oil in selected_super:
                    recipe[oil] = per_super
                remaining_oz -= super_total
            
            # Specialty oils (Argan, Neem): 2-5%
            if selected_specialty:
                specialty_total = min(total_oz * 0.05, remaining_oz)
                per_specialty = specialty_total / len(selected_specialty)
                for oil in selected_specialty:
                    recipe[oil] = per_specialty
                remaining_oz -= specialty_total
            
            # Distribute any remaining weight among all oils in recipe
            if remaining_oz > 0.01 and recipe:
                per_oil = remaining_oz / len(recipe)
                for oil in recipe:
                    recipe[oil] += per_oil
        
        # Round to 2 decimal places
        return {oil: round(weight, 2) for oil, weight in recipe.items()}
    
    @staticmethod
    def generate_targeted_recipe(selected_oils: List[str], total_oz: float, target_props: Dict) -> Dict[str, float]:
        """
        Generate recipe targeting specific property values.
        Uses iterative adjustment to match desired properties.
        """
        # Start with balanced recipe
        recipe = {}
        
        # Categorize oils
        selected_base = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['base']]
        selected_hard = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['hard']]
        selected_super = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['super_fat']]
        selected_cond = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['conditioning']]
        selected_specialty = [oil for oil in selected_oils if oil in AutoRecipeGenerator.OIL_CATEGORIES['specialty']]
        
        # Get target values and normalize to 0-1 range based on recommended ranges
        target_hardness = target_props.get('hardness', 40)
        target_cleansing = target_props.get('cleansing', 15)
        target_conditioning = target_props.get('conditioning', 55)
        target_bubbly = target_props.get('bubbly', 25)
        target_creamy = target_props.get('creamy', 30)
        
        # Adjust percentages based on targets
        # Strategy: Use the target values to guide ratios, but keep defaults balanced
        # High hardness = more hard oils/fats
        # High cleansing = more coconut (but cap it to avoid over-cleansing)
        # High conditioning = more base oils
        # High bubbly = more coconut
        # High creamy = more animal fats and castor
        
        hardness_factor = (target_hardness - 29) / 25  # Normalize to 0-1 range (29-54)
        cleansing_factor = (target_cleansing - 12) / 10  # Normalize to 0-1 range (12-22)
        conditioning_factor = (target_conditioning - 44) / 25  # Normalize to 0-1 range (44-69)
        bubbly_factor = (target_bubbly - 14) / 32  # Normalize to 0-1 range (14-46)
        creamy_factor = (target_creamy - 16) / 32  # Normalize to 0-1 range (16-48)
        
        # Calculate percentages with better balance
        # For balanced defaults (all factors ~0.5), we want a nice balanced soap
        
        # First, determine what categories are available
        has_base = len(selected_base) > 0
        has_coconut = 'Coconut Oil' in selected_hard
        has_other_hard = len([o for o in selected_hard if o != 'Coconut Oil']) > 0
        has_animal = len(selected_cond) > 0
        has_castor = len(selected_super) > 0
        has_specialty = len(selected_specialty) > 0
        
        # Base oils (olive, sunflower, almond) - conditioning
        # Default 40%, goes up to 60% for high conditioning
        base_pct = (0.30 + (conditioning_factor * 0.30)) if has_base else 0  # 30-60%
        
        # Coconut oil - provides cleansing and bubbly but should be limited
        # Default 20%, can go up to 50% max for very high cleansing/bubbly
        # Taking max of cleansing and bubbly needs to achieve target
        coconut_need = max(cleansing_factor, bubbly_factor)
        coconut_pct = (0.15 + (coconut_need * 0.35)) if has_coconut else 0  # 15-50%
        
        # Hard fats (palm, cocoa butter, shea) - hardness without high cleansing
        # Default 15%, goes up with hardness
        hard_pct = (0.10 + (hardness_factor * 0.15)) if has_other_hard else 0  # 10-25%
        
        # Animal fats (lard, tallow) - creamy lather and conditioning
        # Default 15%, increases with creamy
        animal_pct = (0.10 + (creamy_factor * 0.20)) if has_animal else 0  # 10-30%
        
        # Castor oil - creamy, stable lather
        # Default 5%, up to 10% for very creamy
        castor_pct = (0.05 + (creamy_factor * 0.05)) if has_castor else 0  # 5-10%
        
        # Specialty oils (argan, neem) - luxury conditioning
        # Default 3%, can go up to 5% for high conditioning
        specialty_pct = (0.03 + (conditioning_factor * 0.02)) if has_specialty else 0  # 3-5%
        
        # If no base oils, we need to reduce coconut and increase other conditioning oils
        # to compensate for missing conditioning
        if not has_base:
            # Reduce coconut to prevent over-cleansing
            if has_coconut:
                coconut_pct = coconut_pct * 0.6  # Reduce by 40%
            # Increase animal fats and other hard oils for conditioning
            if has_animal:
                animal_pct = animal_pct * 1.8  # Increase significantly
            if has_other_hard:
                hard_pct = hard_pct * 1.5  # Increase moderately
        
        # Normalize to 100%
        total_pct = base_pct + coconut_pct + hard_pct + animal_pct + castor_pct + specialty_pct
        if total_pct > 0:
            base_pct /= total_pct
            coconut_pct /= total_pct
            hard_pct /= total_pct
            animal_pct /= total_pct
            castor_pct /= total_pct
            specialty_pct /= total_pct
        
        # Allocate oils based on categories and what's available
        recipe = {}
        
        # Base oils (olive, sunflower, almond)
        if selected_base:
            base_total = total_oz * base_pct
            per_base = base_total / len(selected_base)
            for oil in selected_base:
                recipe[oil] = per_base
        
        # Coconut - handle specially to avoid over-allocation
        if 'Coconut Oil' in selected_hard:
            recipe['Coconut Oil'] = total_oz * coconut_pct
            # Remove coconut from selected_hard for later processing
            selected_hard = [o for o in selected_hard if o != 'Coconut Oil']
        
        # Other hard oils (palm, cocoa butter, shea)
        if selected_hard:
            hard_total = total_oz * hard_pct
            per_hard = hard_total / len(selected_hard)
            for oil in selected_hard:
                recipe[oil] = recipe.get(oil, 0) + per_hard
        
        # Animal fats (lard, tallow)
        if selected_cond:
            animal_total = total_oz * animal_pct
            per_animal = animal_total / len(selected_cond)
            for oil in selected_cond:
                recipe[oil] = recipe.get(oil, 0) + per_animal
        
        # Castor oil
        if selected_super:
            castor_total = total_oz * castor_pct
            per_castor = castor_total / len(selected_super)
            for oil in selected_super:
                recipe[oil] = recipe.get(oil, 0) + per_castor
        
        # Specialty oils (argan, neem)
        if selected_specialty:
            specialty_total = total_oz * specialty_pct
            per_specialty = specialty_total / len(selected_specialty)
            for oil in selected_specialty:
                recipe[oil] = recipe.get(oil, 0) + per_specialty
        
        # Normalize to exact total
        current_total = sum(recipe.values())
        if current_total > 0:
            factor = total_oz / current_total
            recipe = {oil: weight * factor for oil, weight in recipe.items()}
        
        return {oil: round(weight, 2) for oil, weight in recipe.items()}


class SoapMakerAutoApp:
    """Main application window for auto recipe generator."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Soap Maker - Auto Recipe Generator")
        self.root.geometry("1400x900")
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Initialize paths
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.oils_path = os.path.join(self.base_path, 'data', 'oils.json')
        self.recipes_path = os.path.join(self.base_path, 'data', 'recipes.json')
        self.modifiers_path = os.path.join(self.base_path, 'data', 'modifiers.json')
        self.settings_path = os.path.join(self.base_path, 'config', 'settings.json')
        self.colorants_path = os.path.join(self.base_path, 'data', 'colorants.json')
        
        # Initialize calculator and recipe manager
        self.chemistry = SoapChemistry(self.oils_path, self.modifiers_path)
        self.recipe_manager = RecipeManager(self.recipes_path)
        
        # Load settings and colorants
        self.load_settings()
        self.load_colorants()
        
        # Oil checkboxes storage {oil_name: checkbox_var}
        self.oil_checkboxes = {}
        
        # Property sliders storage
        self.property_sliders = {}
        
        # Property information for tooltips
        self.property_info = {
            'hardness': {
                'description': 'How firm and long-lasting the bar will be. Higher values make harder bars that last longer in the shower.',
                'best_oils': 'Coconut (79), Cocoa Butter (60), Beef Tallow (58), Palm (49), Lard (48), Shea Butter (47)'
            },
            'cleansing': {
                'description': 'Ability to remove oils and dirt from skin. Too high can be drying. Best range: 12-22.',
                'best_oils': 'Coconut Oil (67) - only oil that provides significant cleansing'
            },
            'conditioning': {
                'description': 'How moisturizing the soap is. Higher values are more gentle and moisturizing for skin.',
                'best_oils': 'Castor (90), Olive (82), Sweet Almond (70), Sunflower (67), Shea (56)'
            },
            'bubbly': {
                'description': 'Creates big, fluffy bubbles. Makes soap feel more luxurious but bubbles dissipate quickly.',
                'best_oils': 'Coconut Oil (67) - primary source of large bubbles'
            },
            'creamy': {
                'description': 'Stable, dense, lotion-like lather. Creates rich, lasting bubbles that feel luxurious.',
                'best_oils': 'Cocoa Butter (60), Beef Tallow (58), Palm (49), Lard (48), Shea Butter (47)'
            },
            'longevity': {
                'description': 'How long the soap bar lasts before dissolving. Related to hardness but also fatty acid profile.',
                'best_oils': 'Cocoa Butter (60), Beef Tallow (58), Palm (49), Lard (48) - high stearic/palmitic acids'
            }
        }
        
        # Current generated recipe
        self.current_recipe_oils = {}
        
        # Create GUI
        self.create_widgets()
        
    def load_settings(self):
        """Load application settings."""
        try:
            with open(self.settings_path, 'r') as f:
                self.settings = json.load(f)
        except:
            self.settings = {
                'default_superfat': 5,
                'default_lye_concentration': 33,
                'default_fragrance_percentage': 3
            }
    
    def load_colorants(self):
        """Load colorants database."""
        try:
            with open(self.colorants_path, 'r') as f:
                self.colorants_data = json.load(f)
        except:
            self.colorants_data = {'colorants': [], 'color_spectrum': []}
    
    def create_widgets(self):
        """Create all GUI widgets."""
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Automatic Recipe Generator", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Select oils/fats you want to use and enter batch size. A balanced recipe will be generated automatically!",
                                font=('Arial', 10))
        instructions.pack(pady=5)
        
        # Content frame with left and right panels
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True, pady=10)
        
        # Left panel - Oil selection and batch size
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.create_left_panel(left_frame)
        
        # Right panel - Results
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        self.create_right_panel(right_frame)
    
    def create_left_panel(self, parent):
        """Create the left panel with oil selection."""
        
        # Create canvas for scrolling
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Recipe name
        name_frame = ttk.Frame(scrollable_frame)
        name_frame.pack(fill='x', pady=5, padx=5)
        ttk.Label(name_frame, text="Recipe Name:", font=('Arial', 9, 'bold')).pack(anchor='w')
        self.recipe_name_var = tk.StringVar(value="Auto Generated Recipe")
        ttk.Entry(name_frame, textvariable=self.recipe_name_var, width=40).pack(fill='x', pady=2)
        
        # Soap Type Selector
        type_frame = ttk.LabelFrame(scrollable_frame, text="Quick Start: Base Soap Type", padding=5)
        type_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(type_frame, text="Select a base recipe type:", font=('Arial', 8)).pack(anchor='w', pady=2)
        
        self.soap_types = {
            "-- Custom (select oils manually) --": [],
            "Castile (100% Olive Oil)": ["Olive Oil"],
            "Bastile (Mostly Olive)": ["Olive Oil", "Coconut Oil", "Castor Oil"],
            "Balanced Basic": ["Olive Oil", "Coconut Oil", "Palm Oil"],
            "Lard Basic": ["Lard", "Coconut Oil", "Olive Oil"],
            "Tallow Basic": ["Beef Tallow", "Coconut Oil", "Olive Oil"],
            "Luxury Creamy": ["Olive Oil", "Coconut Oil", "Shea Butter", "Castor Oil"],
            "Vegan Gentle": ["Olive Oil", "Coconut Oil", "Sunflower Oil", "Shea Butter"],
            "Hard Bar": ["Palm Oil", "Coconut Oil", "Cocoa Butter", "Olive Oil"],
            "Conditioning": ["Sweet Almond Oil", "Olive Oil", "Coconut Oil", "Shea Butter"],
            "Andre Soap": ["Coconut Oil", "Palm Oil", "Olive Oil", "Cocoa Butter", "Castor Oil"],
        }
        
        self.soap_type_var = tk.StringVar(value="-- Custom (select oils manually) --")
        type_dropdown = ttk.Combobox(type_frame, textvariable=self.soap_type_var, 
                                     values=list(self.soap_types.keys()), 
                                     state='readonly', width=38)
        type_dropdown.pack(fill='x', pady=2)
        type_dropdown.bind('<<ComboboxSelected>>', self.on_soap_type_selected)
        
        # Scent Profile Selector
        scent_frame = ttk.LabelFrame(scrollable_frame, text="Quick Start: Scent Profile", padding=5)
        scent_frame.pack(fill='x', pady=5, padx=5)
        
        ttk.Label(scent_frame, text="Select a fragrance profile:", font=('Arial', 8)).pack(anchor='w', pady=2)
        
        # Base scent profiles (drops are for 1 pound of oils)
        self.scent_profiles = {
            "-- No Fragrance / Unscented --": {
                "description": "Pure, natural soap scent from oils",
                "notes": "Perfect for sensitive skin or those who prefer unscented products",
                "recipe": []
            },
            "Lavender Bliss": {
                "description": "Calming, relaxing, great for bedtime. Classic spa scent.",
                "notes": "Calming, relaxing, great for bedtime. Classic spa scent.",
                "recipe": [("Lavender", 40), ("Peppermint", 10)]
            },
            "Citrus Fresh": {
                "description": "Bright, uplifting, energizing. Perfect morning soap.",
                "notes": "Bright, uplifting, energizing. Perfect morning soap.",
                "recipe": [("Sweet Orange", 30), ("Lemon", 15), ("Grapefruit", 5)]
            },
            "Eucalyptus Mint": {
                "description": "Invigorating, cooling, refreshing. Great for shower.",
                "notes": "Invigorating, cooling, refreshing. Great for shower.",
                "recipe": [("Eucalyptus", 25), ("Peppermint", 20), ("Tea Tree", 5)]
            },
            "Floral Garden": {
                "description": "Sweet, romantic, feminine. Gentle floral blend.",
                "notes": "Sweet, romantic, feminine. Gentle floral blend.",
                "recipe": [("Lavender", 25), ("Geranium", 15), ("Ylang Ylang", 10)]
            },
            "Woodsy Spice": {
                "description": "Warm, masculine, earthy. Perfect for fall/winter.",
                "notes": "Warm, masculine, earthy. Perfect for fall/winter.",
                "recipe": [("Cedarwood", 20), ("Cinnamon", 15), ("Clove", 10), ("Orange", 5)]
            },
            "Tea Tree Therapy": {
                "description": "Cleansing, purifying, antibacterial. Great for problem skin.",
                "notes": "Cleansing, purifying, antibacterial. Great for problem skin.",
                "recipe": [("Tea Tree", 30), ("Lavender", 15), ("Rosemary", 5)]
            },
            "Rose Garden": {
                "description": "Rose-like scent (more affordable than true rose). Luxurious.",
                "notes": "Rose-like scent (more affordable than true rose). Luxurious.",
                "recipe": [("Geranium", 25), ("Palmarosa", 15), ("Lavender", 10)]
            },
            "Ocean Breeze": {
                "description": "Fresh, clean, breezy. Light and refreshing.",
                "notes": "Fresh, clean, breezy. Light and refreshing.",
                "recipe": [("Litsea", 25), ("Peppermint", 15), ("Eucalyptus", 10)]
            },
            "Patchouli Earth": {
                "description": "Deep, earthy, grounding. Bohemian classic.",
                "notes": "Deep, earthy, grounding. Bohemian classic.",
                "recipe": [("Patchouli", 25), ("Cedarwood", 15), ("Orange", 10)]
            },
            "Vanilla Oatmeal": {
                "description": "Sweet, comforting, gentle. Great for sensitive skin.",
                "notes": "Use Vanilla FO (3% of oils) + add 2 tbsp colloidal oatmeal per pound",
                "recipe": []
            },
            "Baby Gentle": {
                "description": "Ultra-mild for babies and sensitive skin. Use low percentage.",
                "notes": "Ultra-mild for babies and sensitive skin. Use low percentage.",
                "recipe": [("Chamomile", 15), ("Lavender", 10)]
            },
            "Chuberts Pine Tar": {
                "description": "Rustic, woodsy, therapeutic. Traditional pine tar soap scent.",
                "notes": "Deep pine and smoky wood notes. Great for outdoor enthusiasts and skin irritations.",
                "recipe": [("Pine Needle", 25), ("Cedarwood", 15), ("Vetiver", 8), ("Patchouli", 2)]
            },
            "Andre Stank": {
                "description": "Exotic, woodsy, spicy. Sophisticated masculine blend.",
                "notes": "Floral ylang ylang balanced with woods and spice. Pairs perfectly with Andre Soap base for maximum scent retention.",
                "recipe": [("Cedarwood", 18), ("Pine Needle", 12), ("Ylang Ylang", 8), ("Clove", 3)]
            }
        }
        
        self.scent_profile_var = tk.StringVar(value="-- No Fragrance / Unscented --")
        scent_dropdown = ttk.Combobox(scent_frame, textvariable=self.scent_profile_var, 
                                      values=list(self.scent_profiles.keys()), 
                                      state='readonly', width=38)
        scent_dropdown.pack(fill='x', pady=2)
        scent_dropdown.bind('<<ComboboxSelected>>', self.on_scent_profile_selected)
        
        # Scent description display
        self.scent_desc_label = ttk.Label(scent_frame, text="", 
                                          font=('Arial', 7, 'italic'), 
                                          foreground='#2c5aa0',
                                          wraplength=300)
        self.scent_desc_label.pack(anchor='w', pady=2, padx=5)
        
        self.scent_notes_label = ttk.Label(scent_frame, text="", 
                                           font=('Arial', 7), 
                                           foreground='#666',
                                           wraplength=300)
        self.scent_notes_label.pack(anchor='w', pady=2, padx=5)
        
        # Scent Strength selector
        strength_frame = ttk.Frame(scent_frame)
        strength_frame.pack(fill='x', pady=5)
        
        ttk.Label(strength_frame, text="Scent Strength:", font=('Arial', 8)).pack(side='left', padx=(0, 10))
        
        self.scent_strength_var = tk.StringVar(value="Medium")
        self.scent_strengths = {
            "Light/Mild": 3,
            "Medium": 5,
            "Strong": 7
        }
        
        for strength, percentage in self.scent_strengths.items():
            rb = ttk.Radiobutton(strength_frame, text=f"{strength} ({percentage}%)", 
                                variable=self.scent_strength_var, value=strength,
                                command=self.on_scent_strength_changed)
            rb.pack(side='left', padx=5)
        
        # Batch size
        batch_frame = ttk.LabelFrame(scrollable_frame, text="Batch Size", padding=5)
        batch_frame.pack(fill='x', pady=5, padx=5)
        
        size_input_frame = ttk.Frame(batch_frame)
        size_input_frame.pack(fill='x')
        
        ttk.Label(size_input_frame, text="Total Pounds:", font=('Arial', 9)).pack(side='left', padx=3)
        self.batch_size_var = tk.StringVar(value="2")
        batch_entry = ttk.Entry(size_input_frame, textvariable=self.batch_size_var, width=8)
        batch_entry.pack(side='left', padx=3)
        ttk.Label(size_input_frame, text="lbs").pack(side='left')
        
        # Add trace to update scent recipe when batch size changes
        self.batch_size_var.trace_add('write', lambda *args: self.on_batch_size_changed())
        
        # Oil selection - organized by property categories
        oils_frame = ttk.LabelFrame(scrollable_frame, text="Select Oils/Fats by Property", padding=5)
        oils_frame.pack(fill='x', pady=5, padx=5)
        
        # Scrollable frame for oils with fixed height
        oil_canvas = tk.Canvas(oils_frame, height=200)
        oil_scrollbar = ttk.Scrollbar(oils_frame, orient="vertical", command=oil_canvas.yview)
        oil_scroll_frame = ttk.Frame(oil_canvas)
        
        oil_scroll_frame.bind(
            "<Configure>",
            lambda e: oil_canvas.configure(scrollregion=oil_canvas.bbox("all"))
        )
        
        oil_canvas.create_window((0, 0), window=oil_scroll_frame, anchor="nw")
        oil_canvas.configure(yscrollcommand=oil_scrollbar.set)
        
        oil_canvas.pack(side="left", fill="both", expand=True)
        oil_scrollbar.pack(side="right", fill="y")
        
        # Define oil categories with their properties
        oil_categories = [
            {
                'name': 'BASE OILS - Conditioning & Moisturizing',
                'description': '(High conditioning, gentle on skin)',
                'oils': ['Olive Oil', 'Sunflower Oil', 'Sweet Almond Oil', 'Apricot Kernel Oil', 
                        'Avocado Oil', 'Argan Oil', 'Grapeseed Oil', 'Hemp Seed Oil', 'Hazelnut Oil',
                        'Rice Bran Oil', 'Canola Oil', 'Safflower Oil', 'Macadamia Nut Oil']
            },
            {
                'name': 'HARD OILS - Firmness & Structure',
                'description': '(Hardness, long-lasting bars)',
                'oils': ['Cocoa Butter', 'Palm Oil', 'Shea Butter', 'Mango Butter']
            },
            {
                'name': 'CLEANSING & LATHER - Bubbly Soap',
                'description': '(Cleansing power, fluffy bubbles)',
                'oils': ['Coconut Oil', 'Babassu Oil']
            },
            {
                'name': 'CREAMY LATHER - Stable Dense Foam',
                'description': '(Creamy texture, conditioning)',
                'oils': ['Lard', 'Beef Tallow', 'Beeswax']
            },
            {
                'name': 'SPECIALTY - Lather Booster & Unique Properties',
                'description': '(Stable lather, special benefits)',
                'oils': ['Castor Oil', 'Jojoba Oil', 'Neem Oil']
            }
        ]
        
        # Create checkboxes organized by category
        available_oils = self.chemistry.get_available_oils()
        
        for category in oil_categories:
            # Category header
            cat_frame = ttk.Frame(oil_scroll_frame)
            cat_frame.pack(fill='x', pady=(8, 2), padx=3)
            
            ttk.Label(cat_frame, text=category['name'], 
                     font=('Arial', 8, 'bold'), foreground='#2c5aa0').pack(anchor='w')
            ttk.Label(cat_frame, text=category['description'], 
                     font=('Arial', 7, 'italic'), foreground='#666').pack(anchor='w')
            
            # Oil checkboxes in this category
            for oil_name in category['oils']:
                if oil_name in available_oils:
                    oil_frame = ttk.Frame(oil_scroll_frame)
                    oil_frame.pack(fill='x', pady=1, padx=15)
                    
                    var = tk.BooleanVar(value=False)
                    checkbox = ttk.Checkbutton(oil_frame, text=oil_name, variable=var)
                    checkbox.pack(side='left')
                    
                    self.oil_checkboxes[oil_name] = var
        
        # Select All / Deselect All buttons
        button_frame = ttk.Frame(oils_frame)
        button_frame.pack(fill='x', pady=5)
        
        ttk.Button(button_frame, text="Select All", command=self.select_all_oils).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Deselect All", command=self.deselect_all_oils).pack(side='left', padx=5)
        
        # Parameters
        params_frame = ttk.LabelFrame(scrollable_frame, text="Parameters", padding=5)
        params_frame.pack(fill='x', pady=5, padx=5)
        
        # Superfat
        ttk.Label(params_frame, text="Superfat %:", font=('Arial', 8)).grid(row=0, column=0, sticky='w', pady=2, padx=3)
        self.superfat_var = tk.StringVar(value=str(self.settings.get('default_superfat', 5)))
        ttk.Entry(params_frame, textvariable=self.superfat_var, width=8).grid(row=0, column=1, pady=2)
        
        # Lye concentration
        ttk.Label(params_frame, text="Lye Conc %:", font=('Arial', 8)).grid(row=1, column=0, sticky='w', pady=2, padx=3)
        self.lye_conc_var = tk.StringVar(value=str(self.settings.get('default_lye_concentration', 33)))
        ttk.Entry(params_frame, textvariable=self.lye_conc_var, width=8).grid(row=1, column=1, pady=2)
        
        # Fragrance
        ttk.Label(params_frame, text="Fragrance %:", font=('Arial', 8)).grid(row=2, column=0, sticky='w', pady=2, padx=3)
        self.fragrance_var = tk.StringVar(value=str(self.settings.get('default_fragrance_percentage', 3)))
        ttk.Entry(params_frame, textvariable=self.fragrance_var, width=8).grid(row=2, column=1, pady=2)
        
        # Soap Property Modifiers with Sliders
        modifiers_frame = ttk.LabelFrame(scrollable_frame, text="Target Properties", padding=5)
        modifiers_frame.pack(fill='x', pady=5, padx=5)
        
        self.property_sliders = {}
        
        # Hardness slider (29-54, middle = 41.5)
        self.create_slider(modifiers_frame, "Hardness", 0, 29, 54, 0, 
                          "Bar firmness and longevity")
        
        # Cleansing slider (12-22, middle = 17)
        self.create_slider(modifiers_frame, "Cleansing", 1, 12, 22, 0, 
                          "Oil removal power (high = drying)")
        
        # Conditioning slider (44-69, middle = 56.5)
        self.create_slider(modifiers_frame, "Conditioning", 2, 44, 69, 0, 
                          "Moisturizing and skin-friendly")
        
        # Bubbly Lather slider (14-46, middle = 30)
        self.create_slider(modifiers_frame, "Bubbly", 3, 14, 46, 0, 
                          "Large, fluffy bubbles")
        
        # Creamy Lather slider (16-48, middle = 32)
        self.create_slider(modifiers_frame, "Creamy", 4, 16, 48, 0, 
                          "Stable, dense lather")
        
        # Longevity slider (25-50, middle = 37.5)
        self.create_slider(modifiers_frame, "Longevity", 5, 25, 50, 0, 
                          "How long bar lasts in shower")
        
        # Reset button
        reset_btn = ttk.Button(modifiers_frame, text="Reset to Balanced", 
                              command=self.reset_sliders)
        reset_btn.grid(row=6, column=0, columnspan=3, pady=10)
        
        # Natural Colorants Section
        colorants_frame = ttk.LabelFrame(scrollable_frame, text="Natural Colorants (Optional)", padding=5)
        colorants_frame.pack(fill='x', pady=5, padx=5)
        
        # Instructions
        ttk.Label(colorants_frame, text="Select desired color for recommendations:", 
                 font=('Arial', 8)).grid(row=0, column=0, columnspan=3, sticky='w', pady=2)
        
        # Color slider
        color_slider_frame = ttk.Frame(colorants_frame)
        color_slider_frame.grid(row=1, column=0, columnspan=3, sticky='ew', pady=5)
        
        ttk.Label(color_slider_frame, text="Color:", font=('Arial', 8)).pack(side='left', padx=3)
        
        self.color_var = tk.IntVar(value=0)  # 0 = no color selected
        color_slider = ttk.Scale(color_slider_frame, from_=0, to=110, orient='horizontal',
                                variable=self.color_var, length=200)
        color_slider.pack(side='left', padx=5, fill='x', expand=True)
        
        self.color_label = ttk.Label(color_slider_frame, text="None", width=15, font=('Arial', 8))
        self.color_label.pack(side='left', padx=3)
        
        color_slider.config(command=lambda v: self.update_color_display())
        
        # Color preview box
        self.color_preview = tk.Canvas(colorants_frame, width=50, height=20, bg='white', relief='solid', borderwidth=1)
        self.color_preview.grid(row=2, column=0, sticky='w', padx=5, pady=2)
        
        # Colorant recommendations display
        self.colorant_text = tk.Text(colorants_frame, height=4, width=50, font=('Arial', 8), wrap='word')
        self.colorant_text.grid(row=3, column=0, columnspan=3, sticky='ew', padx=5, pady=5)
        self.colorant_text.insert('1.0', 'Move the slider to see colorant recommendations for your desired color.')
        self.colorant_text.config(state='disabled')
        
        # Modifiers/Additives Section
        modifiers_section = ttk.LabelFrame(scrollable_frame, text="Modifiers & Additives (Optional)", padding=5)
        modifiers_section.pack(fill='x', pady=5, padx=5)
        
        # Instructions
        ttk.Label(modifiers_section, text="Select additives to customize your soap:", 
                 font=('Arial', 8, 'bold')).pack(anchor='w', pady=2)
        
        # Create scrollable frame for modifiers
        mod_canvas = tk.Canvas(modifiers_section, height=280)
        mod_scrollbar = ttk.Scrollbar(modifiers_section, orient="vertical", command=mod_canvas.yview)
        mod_scrollable = ttk.Frame(mod_canvas)
        
        mod_scrollable.bind("<Configure>", lambda e: mod_canvas.configure(scrollregion=mod_canvas.bbox("all")))
        mod_canvas.create_window((0, 0), window=mod_scrollable, anchor="nw")
        mod_canvas.configure(yscrollcommand=mod_scrollbar.set)
        
        mod_canvas.pack(side="left", fill="both", expand=True)
        mod_scrollbar.pack(side="right", fill="y")
        
        # Load modifiers
        self.modifier_vars = {}
        self.modifier_amount_vars = {}
        self.modifier_entry_widgets = {}  # Store entry widgets for easy access
        
        modifier_ids = self.chemistry.get_available_modifiers()
        for i, mod_id in enumerate(modifier_ids):
            mod_data = self.chemistry.get_modifier_info(mod_id)
            if not mod_data:
                continue
            
            # Create frame for each modifier
            mod_frame = ttk.Frame(mod_scrollable)
            mod_frame.pack(fill='x', pady=3, padx=5)
            
            # Checkbox
            var = tk.BooleanVar(value=False)
            self.modifier_vars[mod_id] = var
            cb = ttk.Checkbutton(mod_frame, text=mod_data['name'], variable=var,
                               command=lambda mid=mod_id: self.toggle_modifier(mid))
            cb.pack(side='left')
            
            # Info button
            info_btn = tk.Label(mod_frame, text="❓", font=('Arial', 8), cursor="hand2", fg="blue")
            info_btn.pack(side='left', padx=5)
            info_btn.bind("<Button-1>", lambda e, mid=mod_id: self.show_modifier_info(mid))
            
            # Amount entry (disabled by default)
            amount_frame = ttk.Frame(mod_frame)
            amount_frame.pack(side='left', padx=10)
            
            ttk.Label(amount_frame, text="Amount:", font=('Arial', 8)).pack(side='left', padx=2)
            amount_var = tk.StringVar(value=mod_data.get('default_amount', ''))
            self.modifier_amount_vars[mod_id] = amount_var
            amount_entry = ttk.Entry(amount_frame, textvariable=amount_var, width=10, font=('Arial', 8))
            amount_entry.pack(side='left')
            amount_entry.config(state='disabled')
            self.modifier_entry_widgets[mod_id] = amount_entry  # Store reference
            
            ttk.Label(amount_frame, text=mod_data.get('unit', 'g'), 
                     font=('Arial', 8)).pack(side='left', padx=2)
        
        # Add spacer at bottom of scrollable content
        ttk.Frame(scrollable_frame, height=20).pack()
        
        # Action buttons - fixed at bottom outside scroll area
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill='x', pady=5, side='bottom', before=canvas)
        
        # Create buttons in a grid for better visibility
        btn_generate = ttk.Button(action_frame, text="▶ Generate", 
                  command=self.generate_recipe)
        btn_generate.pack(fill='x', padx=5, pady=2)
        
        btn_row = ttk.Frame(action_frame)
        btn_row.pack(fill='x', padx=5)
        
        ttk.Button(btn_row, text="💾 Save", 
                  command=self.save_recipe).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_row, text="📄 PDF", 
                  command=self.export_to_pdf).pack(side='left', padx=2, expand=True, fill='x')
        ttk.Button(btn_row, text="🗑 Clear", 
                  command=self.clear_all).pack(side='left', padx=2, expand=True, fill='x')
    
    def create_slider(self, parent, name, row, min_val, max_val, default_offset, description):
        """Create a property slider with label, value display, and info icon."""
        # Create frame to hold label and info icon
        label_frame = ttk.Frame(parent)
        label_frame.grid(row=row, column=0, sticky='w', padx=3, pady=2)
        
        # Label - more compact
        label = ttk.Label(label_frame, text=f"{name}:", font=('Arial', 8))
        label.pack(side='left')
        
        # Info icon (question mark) - clickable
        info_btn = tk.Label(label_frame, text="❓", font=('Arial', 7), cursor="hand2", fg="blue")
        info_btn.pack(side='left', padx=2)
        
        # Bind click event to show tooltip
        property_key = name.lower().replace(' lather', '').replace(' ', '_')
        info_btn.bind("<Button-1>", lambda e: self.show_property_info(property_key, name))
        
        # Slider - use actual property range
        default_val = (min_val + max_val) / 2 if default_offset == 0 else min_val + (max_val - min_val) * (default_offset / 10)
        slider_var = tk.DoubleVar(value=default_val)
        
        # Scale from min to max of actual property range
        slider = ttk.Scale(parent, from_=min_val, to=max_val, orient='horizontal', 
                          variable=slider_var, length=120)
        slider.grid(row=row, column=1, sticky='ew', padx=3)
        
        # Value label
        value_label = ttk.Label(parent, text=f"{default_val:.0f}", width=6, font=('Arial', 8))
        value_label.grid(row=row, column=2, padx=3)
        
        # Update label when slider moves and auto-add oils
        def update_label(val):
            value_label.config(text=f"{float(val):.0f}")
            self.auto_add_oils_for_properties()
        
        slider.config(command=update_label)
        
        # Store slider info
        property_key = name.lower().replace(' lather', '').replace(' ', '_')
        self.property_sliders[property_key] = {
            'var': slider_var,
            'label': value_label,
            'min': min_val,
            'max': max_val,
            'default': default_val,
            'name': name
        }
    
    def show_property_info(self, property_key, property_name):
        """Show information about a property in a popup window."""
        if property_key not in self.property_info:
            return
            
        info = self.property_info[property_key]
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"{property_name} Information")
        popup.geometry("500x300")
        popup.resizable(False, False)
        
        # Main frame with padding
        main_frame = ttk.Frame(popup, padding="15")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"{property_name}", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_frame = ttk.LabelFrame(main_frame, text="What it does:", padding="10")
        desc_frame.pack(fill='x', pady=5)
        
        desc_text = tk.Text(desc_frame, wrap='word', height=3, font=('Arial', 9))
        desc_text.insert('1.0', info['description'])
        desc_text.config(state='disabled', relief='flat', bg=popup.cget('bg'))
        desc_text.pack(fill='x')
        
        # Best oils
        oils_frame = ttk.LabelFrame(main_frame, text="Best oils/fats (with property values):", padding="10")
        oils_frame.pack(fill='both', expand=True, pady=5)
        
        oils_text = tk.Text(oils_frame, wrap='word', height=6, font=('Arial', 9))
        oils_text.insert('1.0', info['best_oils'])
        oils_text.config(state='disabled', relief='flat', bg=popup.cget('bg'))
        oils_text.pack(fill='both', expand=True)
        
        # Close button
        ttk.Button(main_frame, text="Close", command=popup.destroy).pack(pady=(10, 0))
        
        # Center the popup on parent
        popup.transient(self.root)
        popup.grab_set()
    
    def auto_add_oils_for_properties(self):
        """Automatically select oils needed to achieve target properties."""
        # Get current slider values
        hardness_val = self.property_sliders['hardness']['var'].get()
        cleansing_val = self.property_sliders['cleansing']['var'].get()
        conditioning_val = self.property_sliders['conditioning']['var'].get()
        bubbly_val = self.property_sliders['bubbly']['var'].get()
        creamy_val = self.property_sliders['creamy']['var'].get()
        longevity_val = self.property_sliders['longevity']['var'].get()
        
        # Define thresholds (when to auto-add)
        # High = above 70% of range, Very High = above 85% of range
        
        # Hardness (range: 29-54) - High > 46
        if hardness_val > 46:
            # Add hard oils
            if 'Coconut Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Coconut Oil'].set(True)
            if 'Cocoa Butter' in self.oil_checkboxes:
                self.oil_checkboxes['Cocoa Butter'].set(True)
            if 'Beef Tallow' in self.oil_checkboxes:
                self.oil_checkboxes['Beef Tallow'].set(True)
        
        # Cleansing (range: 12-22) - High > 19
        if cleansing_val > 19:
            if 'Coconut Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Coconut Oil'].set(True)
        
        # Conditioning (range: 44-69) - High > 61
        if conditioning_val > 61:
            if 'Castor Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Castor Oil'].set(True)
            if 'Olive Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Olive Oil'].set(True)
            if 'Sweet Almond Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Sweet Almond Oil'].set(True)
        
        # Bubbly (range: 14-46) - High > 38
        if bubbly_val > 38:
            if 'Coconut Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Coconut Oil'].set(True)
        
        # Creamy (range: 16-48) - High > 40
        if creamy_val > 40:
            if 'Cocoa Butter' in self.oil_checkboxes:
                self.oil_checkboxes['Cocoa Butter'].set(True)
            if 'Beef Tallow' in self.oil_checkboxes:
                self.oil_checkboxes['Beef Tallow'].set(True)
            if 'Lard' in self.oil_checkboxes:
                self.oil_checkboxes['Lard'].set(True)
            if 'Palm Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Palm Oil'].set(True)
        
        # Longevity (range: 25-50) - High > 43
        if longevity_val > 43:
            if 'Cocoa Butter' in self.oil_checkboxes:
                self.oil_checkboxes['Cocoa Butter'].set(True)
            if 'Palm Oil' in self.oil_checkboxes:
                self.oil_checkboxes['Palm Oil'].set(True)
    
    def reset_sliders(self):
        """Reset all sliders to balanced middle values."""
        for prop_name, slider_info in self.property_sliders.items():
            default_val = slider_info['default']
            slider_info['var'].set(default_val)
            slider_info['label'].config(text=f"{default_val:.0f}")
    
    def update_color_display(self):
        """Update the color preview and colorant recommendations based on slider position."""
        position = self.color_var.get()
        
        if position == 0:
            self.color_label.config(text="None")
            self.color_preview.config(bg='white')
            self.colorant_text.config(state='normal')
            self.colorant_text.delete('1.0', 'end')
            self.colorant_text.insert('1.0', 'No colorant selected. Soap will be natural color of oils used.')
            self.colorant_text.config(state='disabled')
            return
        
        # Find the closest color in spectrum
        spectrum = self.colorants_data.get('color_spectrum', [])
        if not spectrum:
            return
        
        # Find closest match
        closest = min(spectrum, key=lambda x: abs(x['position'] - position))
        
        # Update color name and preview
        self.color_label.config(text=closest['name'])
        self.color_preview.config(bg=closest['hex'])
        
        # Get colorant details
        colorants = self.colorants_data.get('colorants', [])
        recommended = []
        for colorant_name in closest['colorants']:
            colorant = next((c for c in colorants if c['name'] == colorant_name), None)
            if colorant:
                recommended.append(colorant)
        
        # Display recommendations
        self.colorant_text.config(state='normal')
        self.colorant_text.delete('1.0', 'end')
        
        if recommended:
            self.colorant_text.insert('end', f"To achieve {closest['name']} color, use:\n\n", 'bold')
            for colorant in recommended:
                self.colorant_text.insert('end', f"• {colorant['name']}: {colorant['usage_rate']}\n")
                self.colorant_text.insert('end', f"  {colorant['notes']}\n", 'italic')
        else:
            self.colorant_text.insert('end', 'No recommendations available for this color.')
        
        self.colorant_text.config(state='disabled')
    
    def on_soap_type_selected(self, event=None):
        """Handle soap type selection and auto-check appropriate oils."""
        selected_type = self.soap_type_var.get()
        print(f"DEBUG: Selected soap type: '{selected_type}'")
        
        if selected_type == "-- Custom (select oils manually) --":
            return  # User wants to manually select
        
        # Get the oils for this soap type
        oils_to_check = self.soap_types[selected_type]
        print(f"DEBUG: Oils to check: {oils_to_check}")
        print(f"DEBUG: Available oil checkboxes: {list(self.oil_checkboxes.keys())}")
        
        # Uncheck all oils first
        for oil_name in self.oil_checkboxes:
            self.oil_checkboxes[oil_name].set(False)
        
        # Check only the oils in the selected type
        for oil_name in oils_to_check:
            if oil_name in self.oil_checkboxes:
                print(f"DEBUG: Checking oil: {oil_name}")
                self.oil_checkboxes[oil_name].set(True)
            else:
                print(f"DEBUG: Oil '{oil_name}' NOT FOUND in oil_checkboxes!")

    
    def get_scaled_scent_recipe(self, profile_name, batch_size_lbs):
        """Get essential oil recipe scaled to batch size."""
        if profile_name not in self.scent_profiles:
            return ""
        
        profile = self.scent_profiles[profile_name]
        recipe = profile.get('recipe', [])
        
        if not recipe:
            return profile.get('description', '')
        
        # Scale drops by batch size (base recipes are for 1 lb)
        scaled_recipe = []
        for oil_name, drops_per_lb in recipe:
            scaled_drops = int(drops_per_lb * batch_size_lbs)
            scaled_recipe.append(f"{scaled_drops} drops {oil_name}")
        
        return " + ".join(scaled_recipe)
    
    def on_batch_size_changed(self):
        """Update scent recipe display when batch size changes."""
        self.on_scent_profile_selected()
    
    def on_scent_strength_changed(self):
        """Update fragrance percentage when scent strength changes."""
        selected_strength = self.scent_strength_var.get()
        if selected_strength in self.scent_strengths:
            new_percentage = self.scent_strengths[selected_strength]
            self.fragrance_var.set(str(new_percentage))
    
    def on_scent_profile_selected(self, event=None):
        """Handle scent profile selection and update description display."""
        selected_profile = self.scent_profile_var.get()
        print(f"DEBUG: Selected scent profile: '{selected_profile}'")
        
        if selected_profile in self.scent_profiles:
            profile_info = self.scent_profiles[selected_profile]
            # Get current batch size for scaling
            try:
                batch_size = float(self.batch_size_var.get())
            except:
                batch_size = 1.0
            
            scaled_recipe = self.get_scaled_scent_recipe(selected_profile, batch_size)
            self.scent_desc_label.config(text=f"Recipe: {scaled_recipe}")
            self.scent_notes_label.config(text=f"Notes: {profile_info['notes']}")
        else:
            self.scent_desc_label.config(text="")
            self.scent_notes_label.config(text="")

    
    def toggle_modifier(self, modifier_id):
        """Enable/disable modifier amount entry based on checkbox state."""
        is_enabled = self.modifier_vars[modifier_id].get()
        
        # Enable/disable the entry widget
        if modifier_id in self.modifier_entry_widgets:
            entry = self.modifier_entry_widgets[modifier_id]
            entry.config(state='normal' if is_enabled else 'disabled')
            
            # If enabling and field is empty, set default value
            if is_enabled:
                current_value = self.modifier_amount_vars[modifier_id].get().strip()
                if not current_value:
                    modifier_info = self.chemistry.get_modifier_info(modifier_id)
                    if modifier_info:
                        default_percent = modifier_info.get('typical_usage_percent', 1.0)
                        
                        # Calculate default amount based on current oils if available
                        if hasattr(self, 'current_recipe_oils') and self.current_recipe_oils:
                            total_oils = sum(self.current_recipe_oils.values())
                            default_amount = total_oils * default_percent / 100
                        else:
                            # Use a typical 1lb batch as default if no recipe yet
                            typical_oils_g = 453.592  # 1 pound in grams
                            default_amount = typical_oils_g * default_percent / 100
                        
                        self.modifier_amount_vars[modifier_id].set(f"{default_amount:.1f}")
        
        # If a recipe exists, recalculate and update properties display
        if hasattr(self, 'current_recipe_oils') and self.current_recipe_oils:
            self.update_properties_display()
    
    def update_properties_display(self):
        """Recalculate properties with current modifiers and update the display."""
        print("DEBUG: update_properties_display() called")
        try:
            # Collect current modifiers
            selected_modifiers = {}
            for mod_id, var in self.modifier_vars.items():
                if var.get():
                    amount_str = self.modifier_amount_vars[mod_id].get()
                    if amount_str:
                        try:
                            amount = float(amount_str)
                            selected_modifiers[mod_id] = amount
                            print(f"DEBUG: Modifier {mod_id} = {amount}g")
                        except ValueError:
                            pass
            
            print(f"DEBUG: Total selected modifiers: {selected_modifiers}")
            
            # Recalculate properties
            base_properties = self.chemistry.calculate_soap_properties(self.current_recipe_oils)
            print(f"DEBUG: Base properties: {base_properties}")
            adjusted_properties = self.chemistry.apply_modifier_effects(base_properties, selected_modifiers)
            print(f"DEBUG: Adjusted properties: {adjusted_properties}")
            print(f"DEBUG: Bubbly changed from {base_properties.get('bubbly', 0)} to {adjusted_properties.get('bubbly', 0)}")
            
            # Get the current text
            current_text = self.results_text.get(1.0, tk.END)
            lines = current_text.split('\n')
            
            # Find and replace property values in "Your Recipe's Properties:" section
            new_lines = []
            in_your_properties = False
            lines_updated = 0
            
            for i, line in enumerate(lines):
                if "Your Recipe's Properties:" in line:
                    in_your_properties = True
                    new_lines.append(line)
                    print(f"DEBUG: Found 'Your Recipe's Properties:' at line {i}")
                elif in_your_properties and line.strip().startswith('-' * 10):
                    # This is the separator line after "Your Recipe's Properties:"
                    new_lines.append(line)
                elif in_your_properties and any(prop in line.lower() for prop in ['hardness', 'cleansing', 'conditioning', 'bubbly', 'creamy', 'iodine', 'ins']):
                    # This is a property line - rebuild it with new value
                    if 'hardness' in line.lower():
                        prop_name = 'hardness'
                        display_name = 'Hardness'
                    elif 'cleansing' in line.lower():
                        prop_name = 'cleansing'
                        display_name = 'Cleansing'
                    elif 'conditioning' in line.lower():
                        prop_name = 'conditioning'
                        display_name = 'Conditioning'
                    elif 'bubbly' in line.lower():
                        prop_name = 'bubbly'
                        display_name = 'Bubbly'
                    elif 'creamy' in line.lower():
                        prop_name = 'creamy'
                        display_name = 'Creamy'
                    elif 'iodine' in line.lower():
                        prop_name = 'iodine'
                        display_name = 'Iodine'
                    elif 'ins' in line.lower():
                        prop_name = 'ins'
                        display_name = 'Ins'
                    else:
                        new_lines.append(line)
                        continue
                    
                    # Get the status symbol from the original line
                    status = ''
                    if '✓' in line:
                        status = '✓'
                    elif '⚠' in line:
                        status = '⚠'
                    elif '✗' in line:
                        status = '✗'
                    
                    # Rebuild the line with new value
                    value = adjusted_properties.get(prop_name, 0)
                    new_line = f"{display_name:.<25} {value:>7.1f} {status}"
                    new_lines.append(new_line)
                    lines_updated += 1
                    print(f"DEBUG: Updated {display_name} from line '{line.strip()}' to '{new_line}'")
                elif in_your_properties and (line.strip() == '' or 'QUALITY ASSESSMENT:' in line):
                    # End of properties section
                    in_your_properties = False
                    new_lines.append(line)
                    print(f"DEBUG: End of properties section at line {i}")
                else:
                    new_lines.append(line)
            
            print(f"DEBUG: Updated {lines_updated} property lines")
            
            # Update the text widget
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, '\n'.join(new_lines))
            print("DEBUG: Text widget updated successfully")
            
        except Exception as e:
            print(f"DEBUG: Error updating properties display: {e}")
            import traceback
            traceback.print_exc()
    
    def show_modifier_info(self, modifier_id):
        """Show detailed information about a modifier."""
        modifier_info = self.chemistry.get_modifier_info(modifier_id)
        if not modifier_info:
            return
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"{modifier_info['name']} Information")
        popup.geometry("550x400")
        popup.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(popup, padding="15")
        main_frame.pack(fill='both', expand=True)
        
        # Title
        ttk.Label(main_frame, text=modifier_info['name'], 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 10))
        
        # Description
        desc_frame = ttk.LabelFrame(main_frame, text="What it does:", padding="10")
        desc_frame.pack(fill='x', pady=5)
        desc_text = tk.Text(desc_frame, wrap='word', height=3, font=('Arial', 9))
        desc_text.insert('1.0', modifier_info['description'])
        desc_text.config(state='disabled', relief='flat', bg=popup.cget('bg'))
        desc_text.pack(fill='x')
        
        # Usage rate
        usage_frame = ttk.LabelFrame(main_frame, text="Usage Rate:", padding="10")
        usage_frame.pack(fill='x', pady=5)
        ttk.Label(usage_frame, text=modifier_info['usage_rate'], 
                 font=('Arial', 9)).pack(anchor='w')
        
        # Benefits
        if 'benefits' in modifier_info and modifier_info['benefits']:
            benefits_frame = ttk.LabelFrame(main_frame, text="Benefits:", padding="10")
            benefits_frame.pack(fill='both', expand=True, pady=5)
            benefits_text = tk.Text(benefits_frame, wrap='word', height=4, font=('Arial', 9))
            for benefit in modifier_info['benefits']:
                benefits_text.insert('end', f"• {benefit}\n")
            benefits_text.config(state='disabled', relief='flat', bg=popup.cget('bg'))
            benefits_text.pack(fill='both', expand=True)
        
        # Notes
        if 'notes' in modifier_info and modifier_info['notes']:
            notes_frame = ttk.LabelFrame(main_frame, text="Important Notes:", padding="10")
            notes_frame.pack(fill='x', pady=5)
            notes_text = tk.Text(notes_frame, wrap='word', height=3, font=('Arial', 9))
            notes_text.insert('1.0', modifier_info['notes'])
            notes_text.config(state='disabled', relief='flat', bg=popup.cget('bg'))
            notes_text.pack(fill='x')
        
        # Close button
        ttk.Button(main_frame, text="Close", command=popup.destroy).pack(pady=(10, 0))
        
        popup.transient(self.root)
        popup.grab_set()
    
    def create_right_panel(self, parent):
        """Create the right panel for results display."""
        
        results_label = ttk.Label(parent, text="Generated Recipe", font=('Arial', 12, 'bold'))
        results_label.pack(pady=5)
        
        self.results_text = scrolledtext.ScrolledText(parent, width=60, height=40, 
                                                      font=('Courier', 9))
        self.results_text.pack(fill='both', expand=True)
    
    def select_all_oils(self):
        """Select all oil checkboxes."""
        for var in self.oil_checkboxes.values():
            var.set(True)
    
    def deselect_all_oils(self):
        """Deselect all oil checkboxes."""
        for var in self.oil_checkboxes.values():
            var.set(False)
    
    def generate_recipe(self):
        """Generate a balanced recipe from selected oils and batch size."""
        print("\n" + "="*60)
        print("GENERATE RECIPE CALLED")
        print("="*60)
        
        try:
            # Get selected oils
            selected_oils = [oil for oil, var in self.oil_checkboxes.items() if var.get()]
            
            if not selected_oils:
                messagebox.showwarning("No Oils Selected", "Please select at least one oil/fat.")
                return
            
            # Get batch size
            batch_size_lbs = float(self.batch_size_var.get())
            if batch_size_lbs <= 0:
                messagebox.showwarning("Invalid Batch Size", "Please enter a positive batch size.")
                return
            
            # Get parameters
            superfat = float(self.superfat_var.get())
            lye_conc = float(self.lye_conc_var.get())
            fragrance_pct = float(self.fragrance_var.get())
            
            # Calculate average SAP value for selected oils to estimate total weight breakdown
            avg_sap = self.calculate_average_sap(selected_oils)
            
            # Calculate the multiplier for total batch weight
            # Total = Oils + Lye + Water + Fragrance
            # Lye = Oils * avg_sap * (1 - superfat/100)
            # Water = Lye * ((100 - lye_conc) / lye_conc)
            # Fragrance = Oils * (fragrance_pct / 100)
            lye_per_oil = avg_sap * (1 - superfat / 100)
            water_per_oil = lye_per_oil * ((100 - lye_conc) / lye_conc)
            fragrance_per_oil = fragrance_pct / 100
            
            total_multiplier = 1 + lye_per_oil + water_per_oil + fragrance_per_oil
            
            # Calculate oil weight from total batch weight
            total_batch_oz = batch_size_lbs * 16
            oil_weight_oz = total_batch_oz / total_multiplier
            
            # Get target properties from sliders
            target_props = {
                'hardness': self.property_sliders['hardness']['var'].get(),
                'cleansing': self.property_sliders['cleansing']['var'].get(),
                'conditioning': self.property_sliders['conditioning']['var'].get(),
                'bubbly': self.property_sliders['bubbly']['var'].get(),
                'creamy': self.property_sliders['creamy']['var'].get(),
            }
            
            # Generate recipe with calculated oil weight and target properties
            recipe_oz = AutoRecipeGenerator.generate_recipe(selected_oils, oil_weight_oz / 16, target_props)
            
            # Convert to grams for calculations
            self.current_recipe_oils = {oil: weight * 28.3495 for oil, weight in recipe_oz.items()}
            
            # Auto-calculate modifier amounts based on actual batch size
            total_oils = sum(self.current_recipe_oils.values())
            print(f"\nDEBUG: Auto-calculating modifier amounts for {total_oils:.2f}g of oils...")
            
            for mod_id, var in self.modifier_vars.items():
                if var.get():  # If checkbox is checked
                    modifier_info = self.chemistry.get_modifier_info(mod_id)
                    if modifier_info:
                        # Calculate appropriate amount based on oil type and total weight
                        usage_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                        
                        if usage_type == 'percent_of_oils':
                            typical_percent = modifier_info.get('typical_usage_percent', 1.0)
                            calculated_amount = total_oils * typical_percent / 100
                            print(f"DEBUG:   {mod_id}: {calculated_amount:.1f}g ({typical_percent}% of {total_oils:.2f}g oils)")
                            self.modifier_amount_vars[mod_id].set(f"{calculated_amount:.1f}")
                        elif usage_type == 'tablespoons_per_pound':
                            # Calculate tablespoons based on pounds of oils
                            total_lbs = total_oils / 453.592
                            default_tbsp_per_lb = modifier_info.get('typical_usage_percent', 1.0)
                            calculated_tbsp = total_lbs * default_tbsp_per_lb
                            print(f"DEBUG:   {mod_id}: {calculated_tbsp:.1f} tbsp ({default_tbsp_per_lb} tbsp/lb × {total_lbs:.2f} lbs)")
                            self.modifier_amount_vars[mod_id].set(f"{calculated_tbsp:.1f}")
            
            # Collect selected modifiers
            selected_modifiers = {}
            print(f"\nDEBUG: Collecting modifiers in generate_recipe...")
            print(f"DEBUG: Number of modifier checkboxes: {len(self.modifier_vars)}")
            for mod_id, var in self.modifier_vars.items():
                is_checked = var.get()
                if is_checked:
                    amount_str = self.modifier_amount_vars[mod_id].get()
                    print(f"DEBUG:   {mod_id}: checked=True, amount_str='{amount_str}'")
                    if amount_str:
                        try:
                            amount = float(amount_str)
                            selected_modifiers[mod_id] = amount
                            print(f"DEBUG:   -> Added: {mod_id} = {amount}g")
                        except ValueError as e:
                            print(f"DEBUG:   -> ValueError: {e}")
                            pass
            
            print(f"DEBUG: Final selected_modifiers for calculation: {selected_modifiers}")
            
            # Calculate actual amounts
            total_oils = sum(self.current_recipe_oils.values())
            print(f"DEBUG: Total oils: {total_oils:.2f}g")
            lye_amount, lye_adjustment = self.chemistry.calculate_lye_amount(self.current_recipe_oils, superfat, selected_modifiers)
            print(f"DEBUG: Lye calculation: base={lye_amount:.2f}g, adjustment={lye_adjustment:.2f}g")
            water_amount = self.chemistry.calculate_water_amount(lye_amount + lye_adjustment, lye_conc)
            fragrance_amount = self.chemistry.calculate_fragrance_amount(total_oils, fragrance_pct)
            properties = self.chemistry.calculate_soap_properties(self.current_recipe_oils)
            # Apply modifier effects to properties
            properties = self.chemistry.apply_modifier_effects(properties, selected_modifiers)
            fatty_acids = self.chemistry.calculate_fatty_acid_profile(self.current_recipe_oils)
            
            # Display results
            self.display_results(recipe_oz, lye_amount, lye_adjustment, water_amount, 
                               fragrance_amount, properties, fatty_acids, superfat, lye_conc,
                               batch_size_lbs, selected_modifiers)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Generation error: {str(e)}")
    
    def calculate_average_sap(self, oil_names):
        """Calculate average SAP value for selected oils."""
        total_sap = 0
        for oil_name in oil_names:
            oil_info = self.chemistry.get_oil_info(oil_name)
            if oil_info:
                total_sap += oil_info.get('sap_naoh', 0.14)
        return total_sap / len(oil_names) if oil_names else 0.14
    
    def display_results(self, oils_oz, lye, lye_adjustment, water, fragrance, props, fatty_acids, superfat, lye_conc, batch_lbs, modifiers=None):
        """Display generated recipe results."""
        self.results_text.delete(1.0, tk.END)
        
        result = "=" * 60 + "\n"
        result += "AUTO-GENERATED SOAP RECIPE\n"
        result += "=" * 60 + "\n\n"
        
        # Calculate total batch weight
        total_oils_oz = sum(oils_oz.values())
        total_lye_g = lye + lye_adjustment
        lye_oz = total_lye_g / 28.3495
        water_oz = water / 28.3495
        fragrance_oz = fragrance / 28.3495
        total_batch_oz = total_oils_oz + lye_oz + water_oz + fragrance_oz
        
        result += f"Total Batch Size: {batch_lbs} lbs ({total_batch_oz:.1f} oz)\n"
        result += f"Recipe: {self.recipe_name_var.get()}\n"
        
        # Show selected soap type if any
        soap_type = self.soap_type_var.get()
        if soap_type and soap_type != "-- Custom (select oils manually) --":
            result += f"Base Type: {soap_type}\n"
        
        # Show selected scent profile if any
        scent_profile = self.scent_profile_var.get()
        if scent_profile and scent_profile != "-- No Fragrance / Unscented --":
            result += f"Scent Profile: {scent_profile}\n"
            if scent_profile in self.scent_profiles:
                profile_info = self.scent_profiles[scent_profile]
                scaled_recipe = self.get_scaled_scent_recipe(scent_profile, batch_lbs)
                result += f"  Recipe: {scaled_recipe}\n"
                result += f"  Notes: {profile_info['notes']}\n"
        
        result += "\n"
        
        # Oils
        result += "OILS:\n"
        result += "-" * 60 + "\n"
        for oil, weight_oz in sorted(oils_oz.items()):
            percentage = (weight_oz / total_oils_oz) * 100
            result += f"{oil:.<35} {weight_oz:>8.2f}oz ({percentage:>5.1f}%)\n"
        result += f"{'Total Oils':.<35} {total_oils_oz:>8.2f}oz\n\n"
        
        # Lye solution
        result += "LYE SOLUTION:\n"
        result += "-" * 60 + "\n"
        if lye_adjustment > 0:
            result += f"{'Base NaOH':.<35} {lye/28.3495:>8.2f}oz\n"
            result += f"{'+ Extra for modifiers':.<35} {lye_adjustment/28.3495:>8.2f}oz\n"
            result += f"{'= Total NaOH':.<35} {lye_oz:>8.2f}oz\n"
        else:
            result += f"{'Sodium Hydroxide (NaOH)':.<35} {lye_oz:>8.2f}oz\n"
        result += f"{'Water':.<35} {water_oz:>8.2f}oz\n"
        result += f"{'Lye Concentration':.<35} {lye_conc:>7.1f}%\n"
        result += f"{'Superfat':.<35} {superfat:>7.1f}%\n\n"
        
        # Fragrance and Modifiers
        result += "ADDITIVES:\n"
        result += "-" * 60 + "\n"
        result += f"{'Fragrance/Essential Oil':.<35} {fragrance_oz:>8.2f}oz\n"
        result += "  When to add: At trace (after blending oils and lye)\n"
        
        # Show essential oil breakdown if scent profile is selected
        scent_profile = self.scent_profile_var.get()
        if scent_profile and scent_profile != "-- No Fragrance / Unscented --":
            if scent_profile in self.scent_profiles:
                profile_info = self.scent_profiles[scent_profile]
                scaled_recipe = self.get_scaled_scent_recipe(scent_profile, batch_lbs)
                if scaled_recipe and profile_info.get('recipe'):
                    result += f"\n  Essential Oil Blend ({scent_profile}):\n"
                    result += f"  {scaled_recipe}\n"
        
        result += "\n  (No modifiers selected - see recommendations below)\n"
        
        if modifiers:
            result += "\nModifiers/Additives:\n"
            result += "\nModifiers/Additives:\n"
            for mod_id, amount in modifiers.items():
                modifier_info = self.chemistry.get_modifier_info(mod_id)
                if modifier_info:
                    result += f"  {modifier_info['name']:.<33} {amount:>8.2f}g ({amount/28.3495:.2f}oz)\n"
                    
                    # Show when to add
                    dissolve_in = modifier_info.get('dissolve_in', '').lower()
                    if 'lye' in dissolve_in:
                        result += f"    When: Dissolve in cooled lye water before adding to oils\n"
                    elif 'oil' in dissolve_in:
                        result += f"    When: Mix with oils before adding lye\n"
                    else:
                        result += f"    When: Add at trace\n"
                    
                    # Show special notes
                    if modifier_info.get('lye_adjustment_factor'):
                        extra_lye = amount * modifier_info['lye_adjustment_factor']
                        result += f"    Note: Extra {extra_lye:.1f}g NaOH already included in lye amount\n"
        else:
            result += "\n  (No modifiers selected - see recommendations below)\n"
        
        result += "\n"
        
        # Weight breakdown
        result += "WEIGHT BREAKDOWN:\n"
        result += "-" * 60 + "\n"
        result += f"{'Oils':.<35} {total_oils_oz:>8.2f}oz ({total_oils_oz/total_batch_oz*100:>5.1f}%)\n"
        result += f"{'Lye':.<35} {lye_oz:>8.2f}oz ({lye_oz/total_batch_oz*100:>5.1f}%)\n"
        result += f"{'Water':.<35} {water_oz:>8.2f}oz ({water_oz/total_batch_oz*100:>5.1f}%)\n"
        result += f"{'Fragrance':.<35} {fragrance_oz:>8.2f}oz ({fragrance_oz/total_batch_oz*100:>5.1f}%)\n"
        result += f"{'TOTAL BATCH':.<35} {total_batch_oz:>8.2f}oz (100.0%)\n\n"
        
        # Properties with quality assessment
        result += "SOAP PROPERTIES:\n"
        result += "=" * 60 + "\n"
        
        # Add recommended ranges header
        result += "Property Ranges for Well-Balanced Soap:\n"
        result += "-" * 60 + "\n"
        ranges = self.settings.get('recommended_ranges', {})
        result += f"{'Hardness':.<25} 29-54 (firmness, longevity)\n"
        result += f"{'Cleansing':.<25} 12-22 (removes oils/dirt)\n"
        result += f"{'Conditioning':.<25} 44-69 (moisturizing)\n"
        result += f"{'Bubbly Lather':.<25} 14-46 (large bubbles)\n"
        result += f"{'Creamy Lather':.<25} 16-48 (stable, dense lather)\n"
        result += f"{'Iodine Value':.<25} 41-70 (softness indicator)\n"
        result += f"{'INS Value':.<25} 136-165 (overall balance)\n"
        result += "\n"
        
        result += "Your Recipe's Properties:\n"
        result += "-" * 60 + "\n"
        
        for prop_name, value in [('hardness', props.get('hardness', 0)),
                                  ('cleansing', props.get('cleansing', 0)),
                                  ('conditioning', props.get('conditioning', 0)),
                                  ('bubbly', props.get('bubbly', 0)),
                                  ('creamy', props.get('creamy', 0)),
                                  ('iodine', props.get('iodine', 0)),
                                  ('ins', props.get('ins', 0))]:
            
            status = self.get_property_status(prop_name, value, ranges)
            result += f"{prop_name.capitalize():.<25} {value:>7.1f} {status}\n"
        
        result += "\n"
        
        # Quality summary
        result += "QUALITY ASSESSMENT:\n"
        result += "-" * 60 + "\n"
        quality_notes = self.assess_recipe_quality(props, ranges)
        for note in quality_notes:
            result += f"• {note}\n"
        
        result += "\n"
        
        # Recommendations for improvement
        recommendations = self.get_modifier_recommendations(props, ranges)
        if recommendations:
            result += "RECOMMENDED MODIFIERS TO IMPROVE YOUR SOAP:\n"
            result += "=" * 60 + "\n"
            for rec in recommendations:
                result += f"• {rec}\n"
            result += "\n"
            result += "HOW TO USE THESE RECOMMENDATIONS:\n"
            result += "-" * 60 + "\n"
            result += "1. Scroll down to the Modifiers & Additives section\n"
            result += "2. Check the checkbox for the modifier you want\n"
            result += "3. Enter the amount shown above (it will auto-fill a default)\n"
            result += "4. Click 'Generate' again to recalculate with modifiers\n"
            result += "5. The modifier will then appear in ADDITIVES section above\n\n"
        
        # pH Information
        result += "pH INFORMATION:\n"
        result += "-" * 60 + "\n"
        result += "Expected pH: 9-10 (typical for properly made soap)\n"
        result += "Note: pH is determined by chemistry, not adjustable.\n"
        result += "After 4-6 week cure, pH should stabilize at 9-10.\n"
        result += "Test with pH strips before use.\n\n"
        
        # Colorants (if selected)
        color_position = self.color_var.get()
        if color_position > 0:
            result += "NATURAL COLORANTS:\n"
            result += "-" * 60 + "\n"
            
            # Find the color in spectrum
            spectrum = self.colorants_data.get('color_spectrum', [])
            closest = min(spectrum, key=lambda x: abs(x['position'] - color_position))
            
            result += f"Target Color: {closest['name']}\n"
            result += f"Recommended Colorants:\n\n"
            
            # Get colorant details
            colorants = self.colorants_data.get('colorants', [])
            for colorant_name in closest['colorants']:
                colorant = next((c for c in colorants if c['name'] == colorant_name), None)
                if colorant:
                    result += f"• {colorant['name']}\n"
                    result += f"  Usage: {colorant['usage_rate']}\n"
                    result += f"  Note: {colorant['notes']}\n"
                    if colorant.get('benefits'):
                        result += f"  Benefits: {colorant['benefits']}\n"
                    result += "\n"
            
            result += "Remember: Add colorants to a small amount of oils first,\n"
            result += "mix well, then add to your soap batter at trace.\n"
            result += "Natural colors may fade or morph over time.\n\n"
        
        self.results_text.insert(1.0, result)
    
    def get_property_status(self, prop_name, value, ranges):
        """Get status indicator for a property value."""
        range_val = ranges.get(prop_name, [])
        if not range_val or len(range_val) != 2:
            return ""
        
        min_val, max_val = range_val
        if min_val <= value <= max_val:
            return "✓"
        elif value < min_val:
            return "⚠ Low"
        else:
            return "⚠ High"
    
    def assess_recipe_quality(self, props, ranges):
        """Assess overall recipe quality and provide recommendations."""
        notes = []
        
        # Hardness
        hardness = props.get('hardness', 0)
        if hardness < 29:
            notes.append("Soap may be soft. Consider adding palm oil, cocoa butter, or coconut oil.")
        elif hardness > 54:
            notes.append("Very hard soap. May be brittle or slow to lather.")
        else:
            notes.append("Good hardness - bar will be firm and long-lasting.")
        
        # Cleansing
        cleansing = props.get('cleansing', 0)
        if cleansing < 12:
            notes.append("Low cleansing. Increase coconut oil for better cleaning power.")
        elif cleansing > 22:
            notes.append("High cleansing. May be drying. Reduce coconut oil or add more conditioning oils.")
        else:
            notes.append("Well-balanced cleansing properties.")
        
        # Conditioning
        conditioning = props.get('conditioning', 0)
        if conditioning < 44:
            notes.append("Add more olive oil, sweet almond, or sunflower for better conditioning.")
        elif conditioning > 69:
            notes.append("Very conditioning but may lack cleansing power.")
        else:
            notes.append("Excellent conditioning - will be gentle on skin.")
        
        # Lather
        bubbly = props.get('bubbly', 0)
        creamy = props.get('creamy', 0)
        if bubbly < 14 and creamy < 16:
            notes.append("Add coconut oil for bubbles or castor oil for creamy lather.")
        else:
            notes.append("Good lather characteristics.")
        
        # Iodine
        iodine = props.get('iodine', 0)
        if iodine > 70:
            notes.append("High iodine value - soap may be prone to rancidity. Use antioxidants.")
        
        return notes
    
    def get_modifier_recommendations(self, props, ranges):
        """Analyze recipe and recommend modifiers to improve it."""
        recommendations = []
        
        # Check properties and suggest modifiers
        hardness = props.get('hardness', 0)
        cleansing = props.get('cleansing', 0)
        conditioning = props.get('conditioning', 0)
        bubbly = props.get('bubbly', 0)
        creamy = props.get('creamy', 0)
        iodine = props.get('iodine', 0)
        
        # Get total oils for calculations
        total_oils_g = sum(self.current_recipe_oils.values()) if hasattr(self, 'current_recipe_oils') and self.current_recipe_oils else 0
        total_oils_lbs = total_oils_g / 453.592 if total_oils_g > 0 else 0
        
        # Hardness improvements
        if hardness < 35:
            # Sodium Lactate: 2% of oils
            amount_g = total_oils_g * 0.02
            recommendations.append(f"SODIUM LACTATE: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) - Adds hardness, faster unmolding")
            
            # Salt: 2% of oils  
            amount_g = total_oils_g * 0.02
            recommendations.append(f"SALT: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) - Creates harder bars with texture")
        
        # Lather improvements
        if bubbly < 20:
            # Sugar: 2% of oils
            amount_g = total_oils_g * 0.02
            recommendations.append(f"SUGAR: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz or {amount_g/5:.1f} tsp) - Boosts bubble production")
        
        if creamy < 20:
            # Sugar also helps creamy lather
            amount_g = total_oils_g * 0.02
            recommendations.append(f"SUGAR: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz or {amount_g/5:.1f} tsp) - Increases creamy lather")
        
        # Skin feel improvements
        if conditioning < 50:
            # Colloidal Oatmeal: 1 tbsp per pound
            amount_tbsp = total_oils_lbs * 1.0
            recommendations.append(f"COLLOIDAL OATMEAL: {amount_tbsp:.1f} tbsp - Soothing and gentle exfoliation")
            
            # Kaolin Clay: 1 tbsp per pound
            amount_tbsp = total_oils_lbs * 1.0
            recommendations.append(f"KAOLIN CLAY: {amount_tbsp:.1f} tbsp - Silky feel and skin benefits")
        
        # Luxury additions (always beneficial)
        if not any('SILK' in r for r in recommendations):
            # Silk: 1 tsp per pound
            amount_tsp = total_oils_lbs * 1.0
            recommendations.append(f"SILK PEPTIDES or TUSSAH SILK: {amount_tsp:.1f} tsp - Luxurious silky feel")
        
        # Antioxidant protection
        if iodine > 65:
            # Vitamin E: 1 tsp per pound
            amount_tsp = total_oils_lbs * 1.0
            recommendations.append(f"VITAMIN E: {amount_tsp:.1f} tsp - Prevents rancidity in high-iodine recipes")
        
        # Special purpose
        if cleansing > 18:
            # Bentonite Clay: 1 tbsp per pound
            amount_tbsp = total_oils_lbs * 1.0
            recommendations.append(f"BENTONITE CLAY: {amount_tbsp:.1f} tbsp - Great for oily/acne-prone skin")
        
        # Universal beneficial additions (always show these)
        if total_oils_g > 0:
            # Citric Acid: 1% of oils (with lye adjustment note)
            amount_g = total_oils_g * 0.01
            extra_lye_g = amount_g * 0.6
            recommendations.append(f"CITRIC ACID: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) + ADD {extra_lye_g:.1f}g extra NaOH - Chelating, longevity")
            
            # Sodium Lactate if not already recommended
            if hardness >= 35:
                amount_g = total_oils_g * 0.02
                recommendations.append(f"SODIUM LACTATE: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) - Faster unmolding, extra hardness")
        
        return recommendations
    
    def save_recipe(self):
        """Save the generated recipe."""
        if not self.current_recipe_oils:
            messagebox.showwarning("No Recipe", "Please generate a recipe first.")
            return
        
        try:
            # Collect modifiers
            selected_modifiers = {}
            for mod_id, var in self.modifier_vars.items():
                if var.get():
                    amount_str = self.modifier_amount_vars[mod_id].get()
                    if amount_str:
                        try:
                            selected_modifiers[mod_id] = float(amount_str)
                        except ValueError:
                            pass
            
            # Create recipe object
            recipe = Recipe(
                name=self.recipe_name_var.get(),
                oils=self.current_recipe_oils,
                superfat=float(self.superfat_var.get()),
                lye_concentration=float(self.lye_conc_var.get()),
                fragrance_percent=float(self.fragrance_var.get()),
                modifiers=selected_modifiers
            )
            
            # Calculate values
            total_oils = sum(self.current_recipe_oils.values())
            recipe.lye_amount, recipe.lye_adjustment = self.chemistry.calculate_lye_amount(self.current_recipe_oils, recipe.superfat, selected_modifiers)
            recipe.water_amount = self.chemistry.calculate_water_amount(recipe.lye_amount + recipe.lye_adjustment, recipe.lye_concentration)
            recipe.fragrance_amount = self.chemistry.calculate_fragrance_amount(total_oils, recipe.fragrance_percent)
            recipe.properties = self.chemistry.calculate_soap_properties(self.current_recipe_oils)
            # Apply modifier effects to properties
            recipe.properties = self.chemistry.apply_modifier_effects(recipe.properties, selected_modifiers)
            recipe.fatty_acids = self.chemistry.calculate_fatty_acid_profile(self.current_recipe_oils)
            
            # Save
            self.recipe_manager.add_recipe(recipe)
            messagebox.showinfo("Success", f"Recipe '{recipe.name}' saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipe: {str(e)}")
    
    def export_to_pdf(self):
        """Export the current recipe to PDF."""
        if not self.current_recipe_oils:
            messagebox.showwarning("No Recipe", "Please generate a recipe first.")
            return
        
        try:
            # Collect modifiers
            selected_modifiers = {}
            print(f"DEBUG: Collecting modifiers...")
            print(f"DEBUG: Available modifier vars: {list(self.modifier_vars.keys())}")
            for mod_id, var in self.modifier_vars.items():
                is_checked = var.get()
                print(f"DEBUG:   {mod_id}: checked={is_checked}")
                if is_checked:
                    amount_str = self.modifier_amount_vars[mod_id].get()
                    print(f"DEBUG:     amount_str='{amount_str}'")
                    if amount_str:
                        try:
                            amount = float(amount_str)
                            selected_modifiers[mod_id] = amount
                            print(f"DEBUG:     Added {mod_id} = {amount}g")
                        except ValueError:
                            print(f"DEBUG:     ValueError converting '{amount_str}'")
                            pass
            
            print(f"DEBUG: Final selected_modifiers: {selected_modifiers}")
            
            # Create recipe object for export
            recipe = Recipe(
                name=self.recipe_name_var.get(),
                oils=self.current_recipe_oils,
                superfat=float(self.superfat_var.get()),
                lye_concentration=float(self.lye_conc_var.get()),
                fragrance_percent=float(self.fragrance_var.get()),
                modifiers=selected_modifiers
            )
            
            print(f"DEBUG: Exporting recipe with modifiers: {selected_modifiers}")
            print(f"DEBUG: Fragrance percent: {recipe.fragrance_percent}%")
            
            # Calculate values
            total_oils = sum(self.current_recipe_oils.values())
            print(f"DEBUG: Total oils: {total_oils}g ({total_oils/28.3495/16:.2f} lbs)")
            recipe.lye_amount, recipe.lye_adjustment = self.chemistry.calculate_lye_amount(self.current_recipe_oils, recipe.superfat, selected_modifiers)
            recipe.water_amount = self.chemistry.calculate_water_amount(recipe.lye_amount + recipe.lye_adjustment, recipe.lye_concentration)
            recipe.fragrance_amount = self.chemistry.calculate_fragrance_amount(total_oils, recipe.fragrance_percent)
            print(f"DEBUG: Calculated fragrance_amount: {recipe.fragrance_amount}g ({recipe.fragrance_amount/28.3495:.2f} oz)")
            recipe.properties = self.chemistry.calculate_soap_properties(self.current_recipe_oils)
            # Apply modifier effects to properties
            recipe.properties = self.chemistry.apply_modifier_effects(recipe.properties, selected_modifiers)
            recipe.fatty_acids = self.chemistry.calculate_fatty_acid_profile(self.current_recipe_oils)
            
            # Get colorant info if selected
            colorant_info = None
            color_position = self.color_var.get()
            print(f"DEBUG: Color position from slider: {color_position}")
            if color_position > 0:
                spectrum = self.colorants_data.get('color_spectrum', [])
                print(f"DEBUG: Color spectrum has {len(spectrum)} entries")
                if spectrum:
                    closest = min(spectrum, key=lambda x: abs(x['position'] - color_position))
                    print(f"DEBUG: Closest color match: {closest['name']}")
                    colorants = self.colorants_data.get('colorants', [])
                    colorant_details = []
                    for colorant_name in closest['colorants']:
                        colorant = next((c for c in colorants if c['name'] == colorant_name), None)
                        if colorant:
                            colorant_details.append(colorant)
                            print(f"DEBUG: Added colorant: {colorant['name']}")
                    colorant_info = {
                        'color_name': closest['name'],
                        'colorants': colorant_details
                    }
                    print(f"DEBUG: Final colorant_info: {colorant_info}")
            else:
                print(f"DEBUG: No color selected (position={color_position})")
            
            # Get scent profile info if selected
            scent_info = None
            scent_profile = self.scent_profile_var.get()
            if scent_profile and scent_profile != "-- No Fragrance / Unscented --":
                if scent_profile in self.scent_profiles:
                    # Use the user's selected batch size for scaling (not calculated from oils alone)
                    batch_lbs = float(self.batch_size_var.get())
                    scaled_recipe = self.get_scaled_scent_recipe(scent_profile, batch_lbs)
                    scent_info = {
                        'name': scent_profile,
                        'recipe': scaled_recipe,
                        'notes': self.scent_profiles[scent_profile]['notes']
                    }
            
            # Get soap type info
            soap_type = self.soap_type_var.get()
            if soap_type == "-- Custom (select oils manually) --":
                soap_type = None
            
            # Export to PDF with colorants and scent
            self.export_recipe_to_pdf_with_colorants(recipe, colorant_info, scent_info, soap_type)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
    
    def export_recipe_to_pdf_with_colorants(self, recipe, colorant_info=None, scent_info=None, soap_type=None):
        """Export recipe to PDF including colorant recommendations."""
        # Get user's desktop as default location
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(desktop):
            desktop = os.path.expanduser("~")
        
        # Create safe filename
        safe_filename = "".join(c for c in recipe.name if c.isalnum() or c in (' ', '-', '_')).strip()
        initial_file = os.path.join(desktop, f"{safe_filename}.pdf")
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=initial_file,
            initialdir=desktop,
            title="Save Recipe as PDF"
        )
        
        if not filename:
            return
        
        try:
            from main import SoapMakerApp
            temp_app = SoapMakerApp.__new__(SoapMakerApp)
            temp_app.settings = self.settings
            temp_app.chemistry = self.chemistry  # Share the chemistry instance
            
            # Store additional info as attributes for PDF export
            if soap_type:
                recipe.soap_type = soap_type
            if scent_info:
                recipe.scent_info = scent_info
            
            # Call the base PDF export
            temp_app.export_recipe_to_pdf_existing_file(recipe, filename, colorant_info)
            
            messagebox.showinfo("Success", f"Recipe exported to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}")
    
    def clear_all(self):
        """Clear all inputs and results."""
        self.recipe_name_var.set("Auto Generated Recipe")
        self.batch_size_var.set("2")
        self.deselect_all_oils()
        self.superfat_var.set(str(self.settings.get('default_superfat', 5)))
        self.lye_conc_var.set(str(self.settings.get('default_lye_concentration', 33)))
        self.fragrance_var.set(str(self.settings.get('default_fragrance_percentage', 3)))
        self.results_text.delete(1.0, tk.END)
        self.current_recipe_oils = {}


def main():
    """Main entry point."""
    root = tk.Tk()
    app = SoapMakerAutoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
