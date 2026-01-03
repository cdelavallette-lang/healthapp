"""
Main GUI application for Soap Making Calculator
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
from typing import Dict
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


class SoapMakerApp:
    """Main application window for soap making calculator."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Soap Maker - Chemistry-Based Recipe Calculator")
        self.root.geometry("1200x900")
        
        # Initialize paths
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.oils_path = os.path.join(self.base_path, 'data', 'oils.json')
        self.recipes_path = os.path.join(self.base_path, 'data', 'recipes.json')
        self.modifiers_path = os.path.join(self.base_path, 'data', 'modifiers.json')
        self.settings_path = os.path.join(self.base_path, 'config', 'settings.json')
        
        # Initialize calculator and recipe manager
        self.chemistry = SoapChemistry(self.oils_path, self.modifiers_path)
        self.recipe_manager = RecipeManager(self.recipes_path)
        
        # Load settings
        self.load_settings()
        
        # Oil entries storage {oil_name: (weight_var, entry_widget)}
        self.oil_entries = {}
        
        # Modifier entries storage {modifier_name: (enabled_var, amount_var, entry_widget)}
        self.modifier_entries = {}
        
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
    
    def create_widgets(self):
        """Create all GUI widgets."""
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tab 1: Recipe Calculator
        calc_frame = ttk.Frame(notebook)
        notebook.add(calc_frame, text='Recipe Calculator')
        self.create_calculator_tab(calc_frame)
        
        # Tab 2: Saved Recipes
        recipes_frame = ttk.Frame(notebook)
        notebook.add(recipes_frame, text='Saved Recipes')
        self.create_recipes_tab(recipes_frame)
        
        # Tab 3: Oil Database
        oils_frame = ttk.Frame(notebook)
        notebook.add(oils_frame, text='Oil Properties')
        self.create_oils_tab(oils_frame)
    
    def create_calculator_tab(self, parent):
        """Create the recipe calculator interface."""
        
        # Create a notebook for subtabs within calculator
        calc_notebook = ttk.Notebook(parent)
        calc_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Subtab 1: Oils & Parameters
        oils_tab = ttk.Frame(calc_notebook)
        calc_notebook.add(oils_tab, text='Oils & Parameters')
        self.create_oils_parameters_subtab(oils_tab)
        
        # Subtab 2: Modifiers & Additives
        modifiers_tab = ttk.Frame(calc_notebook)
        calc_notebook.add(modifiers_tab, text='Modifiers & Additives')
        self.create_modifiers_subtab(modifiers_tab)
        
        # Subtab 3: Results
        results_tab = ttk.Frame(calc_notebook)
        calc_notebook.add(results_tab, text='Results & Actions')
        self.create_results_subtab(results_tab)
    
    def create_oils_parameters_subtab(self, parent):
        """Create the oils and parameters interface."""
        
        # Left panel - Input
        left_frame = ttk.Frame(parent)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        # Recipe name
        ttk.Label(left_frame, text="Recipe Name:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        self.recipe_name_var = tk.StringVar(value="New Recipe")
        ttk.Entry(left_frame, textvariable=self.recipe_name_var, width=40).pack(anchor='w', pady=5)
        
        # Oils section
        oils_label_frame = ttk.LabelFrame(left_frame, text="Oils (in ounces)", padding=10)
        oils_label_frame.pack(fill='both', expand=True, pady=10)
        
        # Scrollable frame for oils
        oils_canvas = tk.Canvas(oils_label_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(oils_label_frame, orient="vertical", command=oils_canvas.yview)
        self.oils_scroll_frame = ttk.Frame(oils_canvas)
        
        self.oils_scroll_frame.bind(
            "<Configure>",
            lambda e: oils_canvas.configure(scrollregion=oils_canvas.bbox("all"))
        )
        
        oils_canvas.create_window((0, 0), window=self.oils_scroll_frame, anchor="nw")
        oils_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enable mousewheel scrolling for oils
        def _on_mousewheel_oils(event):
            oils_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        oils_canvas.bind_all("<MouseWheel>", _on_mousewheel_oils)
        
        oils_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add oil entries
        self.create_oil_entries()
        
        # Parameters section
        params_frame = ttk.LabelFrame(left_frame, text="Parameters", padding=10)
        params_frame.pack(fill='x', pady=10)
        
        # Superfat
        ttk.Label(params_frame, text="Superfat %:").grid(row=0, column=0, sticky='w', pady=3)
        self.superfat_var = tk.StringVar(value=str(self.settings.get('default_superfat', 5)))
        ttk.Entry(params_frame, textvariable=self.superfat_var, width=10).grid(row=0, column=1, pady=3)
        
        # Lye concentration
        ttk.Label(params_frame, text="Lye Concentration %:").grid(row=1, column=0, sticky='w', pady=3)
        self.lye_conc_var = tk.StringVar(value=str(self.settings.get('default_lye_concentration', 33)))
        ttk.Entry(params_frame, textvariable=self.lye_conc_var, width=10).grid(row=1, column=1, pady=3)
        
        # Fragrance
        ttk.Label(params_frame, text="Fragrance %:").grid(row=2, column=0, sticky='w', pady=3)
        self.fragrance_var = tk.StringVar(value=str(self.settings.get('default_fragrance_percentage', 3)))
        ttk.Entry(params_frame, textvariable=self.fragrance_var, width=10).grid(row=2, column=1, pady=3)
        
        # Right panel - Quick info
        right_frame = ttk.Frame(parent)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        info_label = ttk.Label(right_frame, text="Recipe Configuration", font=('Arial', 12, 'bold'))
        info_label.pack(pady=10)
        
        info_text = tk.Text(right_frame, width=50, height=30, wrap=tk.WORD, font=('Arial', 9))
        info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        info_content = """OILS SELECTION GUIDE:

Base Oils (40-70% of recipe):
• Olive Oil - Gentle, conditioning, slow lather
• Sunflower/Safflower - Light, conditioning
• Sweet Almond - Luxurious, gentle

Hard Oils (20-40% of recipe):
• Coconut Oil - Cleansing, bubbles, hardness
• Palm Oil - Hardness, stable lather
• Cocoa/Shea Butter - Hardness, conditioning

Specialty Oils (5-10% of recipe):
• Castor Oil - Boosts lather, adds creaminess
• Avocado Oil - Extra conditioning
• Jojoba - Moisturizing

PARAMETERS:

Superfat (5-8%):
Percentage of oils left unsaponified for extra 
moisturizing. 5% is standard.

Lye Concentration (30-35%):
Higher = less water, faster unmold
33% is a good starting point

Fragrance (3-6%):
3% is standard for most fragrances
Up to 6% for lighter scents

TIP: Once you've entered your oils and parameters,
go to the "Modifiers & Additives" tab to add extras
like citric acid, clays, or sugars, then check 
"Results & Actions" to calculate and export!"""
        
        info_text.insert(1.0, info_content)
        info_text.config(state='disabled')
    
    def create_modifiers_subtab(self, parent):
        """Create the modifiers and additives interface."""
        
        # Left panel - Modifiers list
        left_frame = ttk.Frame(parent)
        left_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Select Modifiers/Additives:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        
        # Modifiers section with much more space
        modifiers_frame = ttk.LabelFrame(left_frame, text="Available Modifiers", padding=10)
        modifiers_frame.pack(fill='both', expand=True, pady=10)
        
        # Scrollable frame for modifiers
        mod_canvas = tk.Canvas(modifiers_frame, highlightthickness=0)
        mod_scrollbar = ttk.Scrollbar(modifiers_frame, orient="vertical", command=mod_canvas.yview)
        self.modifiers_scroll_frame = ttk.Frame(mod_canvas)
        
        self.modifiers_scroll_frame.bind(
            "<Configure>",
            lambda e: mod_canvas.configure(scrollregion=mod_canvas.bbox("all"))
        )
        
        mod_canvas.create_window((0, 0), window=self.modifiers_scroll_frame, anchor="nw")
        mod_canvas.configure(yscrollcommand=mod_scrollbar.set)
        
        # Enable mousewheel scrolling for modifiers
        def _on_mousewheel_mods(event):
            mod_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        mod_canvas.bind_all("<MouseWheel>", _on_mousewheel_mods)
        
        mod_canvas.pack(side="left", fill="both", expand=True)
        mod_scrollbar.pack(side="right", fill="y")
        
        # Add modifier entries
        self.create_modifier_entries()
        
        # Right panel - Modifier info
        right_frame = ttk.Frame(parent)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        
        info_label = ttk.Label(right_frame, text="About Modifiers", font=('Arial', 12, 'bold'))
        info_label.pack(pady=10)
        
        info_text = scrolledtext.ScrolledText(right_frame, width=50, height=35, wrap=tk.WORD, font=('Arial', 9))
        info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        info_content = """MODIFIERS & ADDITIVES:

✓ Citric Acid (Chelating Agent)
  1% of oils - Lowers pH, improves lather in hard water
  ⚠ Automatically adds extra lye (0.6g per 1g citric acid)

✓ Sodium Lactate (Hardener)
  2% of oils - Makes bars harder, easier unmolding

✓ Sugar (Lather Booster)
  3% of oils - Increases bubbles and lather
  Mix into lye water before adding to oils

✓ Salt / Sodium Chloride (Hardener)
  3% of oils (or up to 100% for salt bars)
  Creates very hard bars, reduces lather at high amounts

✓ Kaolin Clay (Additive)
  1% of oils - Adds slip, anchors fragrance, whitens soap
  Mix with oils before adding lye

✓ Bentonite Clay (Additive)
  1% of oils - Detoxifying, grey-green color
  Good for oily skin

✓ Colloidal Oatmeal (Additive)
  1% of oils - Soothing, gentle exfoliation
  Adds tan/beige color with specks

✓ Silk Amino Acids (Luxury)
  0.5% of oils - Adds silky feel and luxury lather

✓ Tussah Silk Fibers (Luxury)
  1 cocoon per batch - Dissolve in hot lye water
  Adds sheen and luxury feel

✓ Vitamin E Oil (Antioxidant)
  0.5% of oils - Extends shelf life, moisturizing

USAGE TIPS:
• Check the box to enable a modifier
• Click the "?" button for detailed information
• Typical amounts are pre-filled but adjustable
• Some modifiers affect color or scent (see info)
• Citric acid lye adjustment is automatic!"""
        
        info_text.insert(1.0, info_content)
        info_text.config(state='disabled')
    
    def create_results_subtab(self, parent):
        """Create the results and action buttons interface."""
        
        # Top frame for buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(button_frame, text="Actions:", font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Calculate Recipe", command=self.calculate_recipe, 
                  style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save Recipe", command=self.save_recipe).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Export to PDF", command=self.export_current_recipe_to_pdf).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_recipe).pack(side='left', padx=5)
        
        # Results display
        results_frame = ttk.Frame(parent)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        results_label = ttk.Label(results_frame, text="Recipe Calculations", font=('Arial', 12, 'bold'))
        results_label.pack(pady=5)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, width=80, height=40, 
                                                      font=('Courier', 9))
        self.results_text.pack(fill='both', expand=True)
        
        # Add initial help text
        help_text = """
═══════════════════════════════════════════════════════════════════════════════
                         SOAP RECIPE CALCULATOR - READY
═══════════════════════════════════════════════════════════════════════════════

GETTING STARTED:

1. Go to "Oils & Parameters" tab
   - Enter your recipe name
   - Fill in oil amounts (in ounces)
   - Adjust superfat, lye concentration, and fragrance percentage

2. Go to "Modifiers & Additives" tab (optional)
   - Check boxes to enable modifiers like citric acid, clays, sugars
   - Adjust amounts as needed
   - Click "?" buttons for detailed information

3. Return to this "Results & Actions" tab
   - Click "Calculate Recipe" to see your complete soap formula
   - Results will show oils, lye solution, additives, and soap properties
   - Use "Save Recipe" to keep it for later
   - Use "Export to PDF" to get a printable recipe with instructions

TIPS:
• Start with 1-2 pounds of total oils for your first batch
• Standard recipe: 60-70% olive oil, 20-30% coconut oil, 5-10% castor oil
• Citric acid automatically adjusts lye - no manual calculation needed!
• All amounts scale automatically based on your batch size

Ready when you are! Enter your oils and click "Calculate Recipe" to begin.
═══════════════════════════════════════════════════════════════════════════════
"""
        self.results_text.insert(1.0, help_text)
    
    
    def create_oil_entries(self):
        """Create entry fields for each oil."""
        available_oils = self.chemistry.get_available_oils()
        
        for i, oil_name in enumerate(available_oils):
            frame = ttk.Frame(self.oils_scroll_frame)
            frame.pack(fill='x', pady=2)
            
            ttk.Label(frame, text=oil_name, width=20).pack(side='left')
            
            var = tk.StringVar(value="0")
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.pack(side='left', padx=5)
            
            ttk.Label(frame, text="oz").pack(side='left')
            
            self.oil_entries[oil_name] = (var, entry)
    
    def create_modifier_entries(self):
        """Create entry fields for each modifier/additive."""
        available_modifiers = self.chemistry.get_available_modifiers()
        
        for modifier_name in available_modifiers:
            frame = ttk.Frame(self.modifiers_scroll_frame)
            frame.pack(fill='x', pady=2)
            
            # Checkbox to enable/disable
            enabled_var = tk.BooleanVar(value=False)
            check = ttk.Checkbutton(frame, variable=enabled_var, 
                                   command=lambda n=modifier_name: self.toggle_modifier(n))
            check.pack(side='left')
            
            # Modifier name
            ttk.Label(frame, text=modifier_name, width=20).pack(side='left')
            
            # Amount entry
            amount_var = tk.StringVar(value="0")
            entry = ttk.Entry(frame, textvariable=amount_var, width=8, state='disabled')
            entry.pack(side='left', padx=5)
            
            # Unit label
            modifier_info = self.chemistry.get_modifier_info(modifier_name)
            unit = "g"
            if modifier_info.get('usage_rate_type') == 'tablespoons_per_pound':
                unit = "tbsp"
            ttk.Label(frame, text=unit).pack(side='left')
            
            # Info button
            info_btn = ttk.Button(frame, text="?", width=2,
                                 command=lambda n=modifier_name: self.show_modifier_info(n))
            info_btn.pack(side='left', padx=2)
            
            self.modifier_entries[modifier_name] = (enabled_var, amount_var, entry)
    
    def toggle_modifier(self, modifier_name):
        """Enable/disable modifier entry when checkbox is toggled."""
        if modifier_name in self.modifier_entries:
            enabled_var, amount_var, entry = self.modifier_entries[modifier_name]
            if enabled_var.get():
                entry.config(state='normal')
                # Set default value
                modifier_info = self.chemistry.get_modifier_info(modifier_name)
                typical_usage = modifier_info.get('typical_usage_percent', 1.0)
                amount_var.set(str(typical_usage))
            else:
                entry.config(state='disabled')
                amount_var.set("0")
    
    def show_modifier_info(self, modifier_name):
        """Show information about a modifier in a popup."""
        modifier = self.chemistry.get_modifier_info(modifier_name)
        if not modifier:
            return
        
        info_window = tk.Toplevel(self.root)
        info_window.title(f"About {modifier_name}")
        info_window.geometry("500x400")
        
        text = scrolledtext.ScrolledText(info_window, wrap=tk.WORD, width=60, height=20)
        text.pack(fill='both', expand=True, padx=10, pady=10)
        
        info_text = f"{modifier_name}\n"
        info_text += "=" * 50 + "\n\n"
        info_text += f"Category: {modifier.get('category', 'N/A')}\n\n"
        info_text += f"Description:\n{modifier.get('description', 'No description')}\n\n"
        
        if 'typical_usage_percent' in modifier:
            info_text += f"Typical Usage: {modifier['typical_usage_percent']}%\n"
            info_text += f"Range: {modifier.get('min_percent', 0)}% - {modifier.get('max_percent', 0)}%\n\n"
        
        if 'lye_adjustment_note' in modifier:
            info_text += f"⚠ Lye Adjustment: {modifier['lye_adjustment_note']}\n\n"
        
        if 'dissolve_in' in modifier:
            info_text += f"Dissolve in: {modifier['dissolve_in']}\n\n"
        
        effects = modifier.get('effects', {})
        if effects:
            info_text += "Effects:\n"
            info_text += "-" * 50 + "\n"
            for effect_type, effect_desc in effects.items():
                info_text += f"  • {effect_type.replace('_', ' ').title()}: {effect_desc}\n"
        
        text.insert(1.0, info_text)
        text.config(state='disabled')
    
    def calculate_recipe(self):
        """Calculate soap recipe based on inputs."""
        try:
            # Get oil weights (convert from ounces to grams for calculations)
            oil_weights = {}
            for oil_name, (var, _) in self.oil_entries.items():
                weight_oz = float(var.get() or 0)
                if weight_oz > 0:
                    oil_weights[oil_name] = weight_oz * 28.3495  # Convert oz to grams
            
            if not oil_weights:
                messagebox.showwarning("No Oils", "Please enter at least one oil weight.")
                return
            
            # Get modifiers
            modifiers = {}
            total_oils = sum(oil_weights.values())
            for modifier_name, (enabled_var, amount_var, _) in self.modifier_entries.items():
                if enabled_var.get():
                    modifier_info = self.chemistry.get_modifier_info(modifier_name)
                    usage_rate_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                    
                    if usage_rate_type == 'percent_of_oils':
                        # Convert percentage to grams
                        percent = float(amount_var.get() or 0)
                        modifiers[modifier_name] = total_oils * percent / 100
                    else:
                        # For other types, store the raw value
                        modifiers[modifier_name] = float(amount_var.get() or 0)
            
            # Get parameters
            superfat = float(self.superfat_var.get())
            lye_conc = float(self.lye_conc_var.get())
            fragrance_pct = float(self.fragrance_var.get())
            
            # Calculate
            lye_amount, lye_adjustment = self.chemistry.calculate_lye_amount(
                oil_weights, superfat, modifiers=modifiers
            )
            water_amount = self.chemistry.calculate_water_amount(lye_amount + lye_adjustment, lye_conc)
            fragrance_amount = self.chemistry.calculate_fragrance_amount(total_oils, fragrance_pct)
            properties = self.chemistry.calculate_soap_properties(oil_weights)
            fatty_acids = self.chemistry.calculate_fatty_acid_profile(oil_weights)
            
            # Display results
            self.display_results(oil_weights, lye_amount, lye_adjustment, water_amount, 
                               fragrance_amount, properties, fatty_acids, superfat, 
                               lye_conc, modifiers)
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
    
    def display_results(self, oils, lye, lye_adjustment, water, fragrance, props, 
                       fatty_acids, superfat, lye_conc, modifiers=None):
        """Display calculation results (convert grams back to ounces for display)."""
        self.results_text.delete(1.0, tk.END)
        
        result = "=" * 50 + "\n"
        result += "SOAP RECIPE CALCULATION RESULTS\n"
        result += "=" * 50 + "\n\n"
        
        # Oils (convert back to ounces)
        result += "OILS:\n"
        result += "-" * 50 + "\n"
        total_oils = sum(oils.values())
        for oil, weight in sorted(oils.items()):
            percentage = (weight / total_oils) * 100
            weight_oz = weight / 28.3495
            result += f"{oil:.<30} {weight_oz:>8.2f}oz ({percentage:>5.1f}%)\n"
        result += f"{'Total Oils':.<30} {total_oils/28.3495:>8.2f}oz\n\n"
        
        # Lye solution (convert to ounces)
        result += "LYE SOLUTION:\n"
        result += "-" * 50 + "\n"
        total_lye = lye + lye_adjustment
        result += f"{'Sodium Hydroxide (NaOH)':.<30} {lye/28.3495:>8.2f}oz\n"
        if lye_adjustment > 0:
            result += f"{'  + Extra for modifiers':.<30} {lye_adjustment/28.3495:>8.2f}oz\n"
            result += f"{'  = Total NaOH':.<30} {total_lye/28.3495:>8.2f}oz\n"
        result += f"{'Water':.<30} {water/28.3495:>8.2f}oz\n"
        result += f"{'Lye Concentration':.<30} {lye_conc:>7.1f}%\n"
        result += f"{'Superfat':.<30} {superfat:>7.1f}%\n\n"
        
        # Fragrance and Modifiers
        result += "ADDITIVES:\n"
        result += "-" * 50 + "\n"
        result += f"{'Fragrance/Essential Oil':.<30} {fragrance/28.3495:>8.2f}oz\n"
        
        if modifiers:
            result += "\nModifiers/Additives:\n"
            for mod_name, amount in modifiers.items():
                modifier_info = self.chemistry.get_modifier_info(mod_name)
                usage_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                
                if usage_type == 'percent_of_oils':
                    result += f"  {mod_name:.<28} {amount:>8.2f}g\n"
                elif usage_type == 'tablespoons_per_pound':
                    result += f"  {mod_name:.<28} {amount:>8.2f}tbsp\n"
                else:
                    result += f"  {mod_name:.<28} {amount:>8.2f}\n"
        result += "\n"
        
        # Properties
        result += "SOAP PROPERTIES:\n"
        result += "-" * 50 + "\n"
        result += f"{'Hardness':.<30} {props.get('hardness', 0):>7.1f}\n"
        result += f"{'Cleansing':.<30} {props.get('cleansing', 0):>7.1f}\n"
        result += f"{'Conditioning':.<30} {props.get('conditioning', 0):>7.1f}\n"
        result += f"{'Bubbly Lather':.<30} {props.get('bubbly', 0):>7.1f}\n"
        result += f"{'Creamy Lather':.<30} {props.get('creamy', 0):>7.1f}\n"
        result += f"{'Iodine':.<30} {props.get('iodine', 0):>7.1f}\n"
        result += f"{'INS':.<30} {props.get('ins', 0):>7.1f}\n\n"
        
        # Recommended ranges
        result += "RECOMMENDED RANGES:\n"
        result += "-" * 50 + "\n"
        ranges = self.settings.get('recommended_ranges', {})
        result += f"Hardness: {ranges.get('hardness', [29, 54])}\n"
        result += f"Cleansing: {ranges.get('cleansing', [12, 22])}\n"
        result += f"Conditioning: {ranges.get('conditioning', [44, 69])}\n"
        result += f"Bubbly: {ranges.get('bubbly', [14, 46])}\n"
        result += f"Creamy: {ranges.get('creamy', [16, 48])}\n\n"
        
        # Recommendations for improvement
        recommendations = self.get_modifier_recommendations(props, ranges)
        if recommendations:
            result += "RECOMMENDED MODIFIERS TO IMPROVE YOUR SOAP:\n"
            result += "=" * 50 + "\n"
            for rec in recommendations:
                result += f"{rec}\n"
            result += "\n"
        
        # Fatty acids
        result += "FATTY ACID PROFILE:\n"
        result += "-" * 50 + "\n"
        for fa, value in sorted(fatty_acids.items()):
            result += f"{fa.capitalize():.<30} {value:>7.1f}%\n"
        
        self.results_text.insert(1.0, result)
    
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
        
        # Get total oils for calculations (from last calculation)
        total_oils_g = 0
        for oil_name, (var, _) in self.oil_entries.items():
            weight_oz = float(var.get() or 0)
            if weight_oz > 0:
                total_oils_g += weight_oz * 28.3495
        
        total_oils_lbs = total_oils_g / 453.592 if total_oils_g > 0 else 0
        
        # Hardness improvements
        if hardness < 35:
            amount_g = total_oils_g * 0.02
            recommendations.append(f"• SODIUM LACTATE: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) - Adds hardness, faster unmolding")
            amount_g = total_oils_g * 0.02
            recommendations.append(f"• SALT: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) - Creates harder bars with texture")
        
        # Lather improvements
        if bubbly < 20:
            amount_g = total_oils_g * 0.02
            recommendations.append(f"• SUGAR: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz or {amount_g/5:.1f} tsp) - Boosts bubble production")
        
        if creamy < 20:
            amount_g = total_oils_g * 0.02
            recommendations.append(f"• SUGAR: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz or {amount_g/5:.1f} tsp) - Increases creamy lather")
        
        # Skin feel improvements
        if conditioning < 50:
            amount_tbsp = total_oils_lbs * 1.0
            recommendations.append(f"• COLLOIDAL OATMEAL: {amount_tbsp:.1f} tbsp - Soothing and gentle exfoliation")
            amount_tbsp = total_oils_lbs * 1.0
            recommendations.append(f"• KAOLIN CLAY: {amount_tbsp:.1f} tbsp - Silky feel and skin benefits")
        
        # Luxury additions
        if not any('SILK' in r for r in recommendations):
            amount_tsp = total_oils_lbs * 1.0
            recommendations.append(f"• SILK PEPTIDES or TUSSAH SILK: {amount_tsp:.1f} tsp - Luxurious silky feel")
        
        # Antioxidant protection
        if iodine > 65:
            amount_tsp = total_oils_lbs * 1.0
            recommendations.append(f"• VITAMIN E: {amount_tsp:.1f} tsp - Prevents rancidity in high-iodine recipes")
        
        # Special purpose
        if cleansing > 18:
            amount_tbsp = total_oils_lbs * 1.0
            recommendations.append(f"• BENTONITE CLAY: {amount_tbsp:.1f} tbsp - Great for oily/acne-prone skin")
        
        # Universal beneficial additions
        if total_oils_g > 0:
            # Citric Acid: 1% of oils
            amount_g = total_oils_g * 0.01
            extra_lye_g = amount_g * 0.6
            recommendations.append(f"• CITRIC ACID: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) + ADD {extra_lye_g:.1f}g extra NaOH - Chelating, longevity")
            
            # Sodium Lactate if not already recommended
            if hardness >= 35:
                amount_g = total_oils_g * 0.02
                recommendations.append(f"• SODIUM LACTATE: {amount_g:.1f}g ({amount_g/28.3495:.2f}oz) - Faster unmolding, extra hardness")
        
        return recommendations
    
    def save_recipe(self):
        """Save current recipe."""
        try:
            # Get oil weights (convert from ounces to grams)
            oil_weights = {}
            for oil_name, (var, _) in self.oil_entries.items():
                weight_oz = float(var.get() or 0)
                if weight_oz > 0:
                    oil_weights[oil_name] = weight_oz * 28.3495  # Convert oz to grams
            
            if not oil_weights:
                messagebox.showwarning("No Oils", "Please enter at least one oil weight.")
                return
            
            # Get modifiers
            modifiers = {}
            total_oils = sum(oil_weights.values())
            for modifier_name, (enabled_var, amount_var, _) in self.modifier_entries.items():
                if enabled_var.get():
                    modifier_info = self.chemistry.get_modifier_info(modifier_name)
                    usage_rate_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                    
                    if usage_rate_type == 'percent_of_oils':
                        percent = float(amount_var.get() or 0)
                        modifiers[modifier_name] = total_oils * percent / 100
                    else:
                        modifiers[modifier_name] = float(amount_var.get() or 0)
            
            # Create recipe
            recipe = Recipe(
                name=self.recipe_name_var.get(),
                oils=oil_weights,
                superfat=float(self.superfat_var.get()),
                lye_concentration=float(self.lye_conc_var.get()),
                fragrance_percent=float(self.fragrance_var.get()),
                modifiers=modifiers
            )
            
            # Calculate values
            recipe.lye_amount, recipe.lye_adjustment = self.chemistry.calculate_lye_amount(
                oil_weights, recipe.superfat, modifiers=modifiers
            )
            recipe.water_amount = self.chemistry.calculate_water_amount(
                recipe.lye_amount + recipe.lye_adjustment, recipe.lye_concentration
            )
            recipe.fragrance_amount = self.chemistry.calculate_fragrance_amount(total_oils, recipe.fragrance_percent)
            recipe.properties = self.chemistry.calculate_soap_properties(oil_weights)
            recipe.fatty_acids = self.chemistry.calculate_fatty_acid_profile(oil_weights)
            
            # Save
            self.recipe_manager.add_recipe(recipe)
            messagebox.showinfo("Success", f"Recipe '{recipe.name}' saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipe: {str(e)}")
    
    def clear_recipe(self):
        """Clear all inputs."""
        self.recipe_name_var.set("New Recipe")
        for var, _ in self.oil_entries.values():
            var.set("0")
        for enabled_var, amount_var, entry in self.modifier_entries.values():
            enabled_var.set(False)
            amount_var.set("0")
            entry.config(state='disabled')
        self.superfat_var.set(str(self.settings.get('default_superfat', 5)))
        self.lye_conc_var.set(str(self.settings.get('default_lye_concentration', 33)))
        self.fragrance_var.set(str(self.settings.get('default_fragrance_percentage', 3)))
        self.results_text.delete(1.0, tk.END)
    
    def create_recipes_tab(self, parent):
        """Create saved recipes interface."""
        # Top frame with buttons
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(top_frame, text="Saved Recipes", font=('Arial', 14, 'bold')).pack(side='left')
        ttk.Button(top_frame, text="Refresh", command=self.refresh_recipes_list).pack(side='right', padx=5)
        ttk.Button(top_frame, text="Delete Selected", command=self.delete_selected_recipe).pack(side='right', padx=5)
        ttk.Button(top_frame, text="Load Recipe", command=self.load_selected_recipe).pack(side='right', padx=5)
        ttk.Button(top_frame, text="Export to PDF", command=self.export_selected_recipe_to_pdf).pack(side='right', padx=5)
        
        # Recipe list frame
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview for recipes
        columns = ('Name', 'Created', 'Oils', 'Superfat')
        self.recipes_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        
        self.recipes_tree.heading('#0', text='#')
        self.recipes_tree.column('#0', width=50)
        self.recipes_tree.heading('Name', text='Recipe Name')
        self.recipes_tree.column('Name', width=250)
        self.recipes_tree.heading('Created', text='Date Created')
        self.recipes_tree.column('Created', width=150)
        self.recipes_tree.heading('Oils', text='Total Oils')
        self.recipes_tree.column('Oils', width=100)
        self.recipes_tree.heading('Superfat', text='Superfat %')
        self.recipes_tree.column('Superfat', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.recipes_tree.yview)
        self.recipes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recipes_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Details frame
        details_frame = ttk.LabelFrame(parent, text="Recipe Details", padding=10)
        details_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.recipe_details_text = scrolledtext.ScrolledText(details_frame, width=80, height=15, 
                                                              font=('Courier', 9))
        self.recipe_details_text.pack(fill='both', expand=True)
        
        # Bind selection event
        self.recipes_tree.bind('<<TreeviewSelect>>', self.on_recipe_select)
        
        # Load recipes
        self.refresh_recipes_list()
    
    def refresh_recipes_list(self):
        """Refresh the saved recipes list."""
        # Clear existing items
        for item in self.recipes_tree.get_children():
            self.recipes_tree.delete(item)
        
        # Reload recipes
        self.recipe_manager.load_recipes()
        
        # Add recipes to tree
        for idx, recipe in enumerate(self.recipe_manager.get_all_recipes()):
            total_oils = sum(recipe.oils.values()) / 28.3495  # Convert to oz
            created = datetime.fromisoformat(recipe.created_date).strftime('%Y-%m-%d %H:%M')
            
            self.recipes_tree.insert('', 'end', text=str(idx + 1),
                                    values=(recipe.name, created, f"{total_oils:.2f} oz", f"{recipe.superfat}%"))
    
    def on_recipe_select(self, event):
        """Handle recipe selection."""
        selection = self.recipes_tree.selection()
        if not selection:
            return
        
        item = self.recipes_tree.item(selection[0])
        idx = int(item['text']) - 1
        
        recipe = self.recipe_manager.get_recipe(idx)
        if recipe:
            self.display_recipe_details(recipe)
    
    def display_recipe_details(self, recipe):
        """Display details of selected recipe."""
        self.recipe_details_text.delete(1.0, tk.END)
        
        details = "=" * 60 + "\n"
        details += f"{recipe.name.upper()}\n"
        details += "=" * 60 + "\n\n"
        
        details += f"Created: {datetime.fromisoformat(recipe.created_date).strftime('%Y-%m-%d %H:%M')}\n"
        details += f"Modified: {datetime.fromisoformat(recipe.modified_date).strftime('%Y-%m-%d %H:%M')}\n\n"
        
        details += "OILS:\n"
        details += "-" * 60 + "\n"
        total_oils = sum(recipe.oils.values())
        for oil, weight in sorted(recipe.oils.items()):
            percentage = (weight / total_oils) * 100
            weight_oz = weight / 28.3495
            details += f"{oil:.<35} {weight_oz:>8.2f}oz ({percentage:>5.1f}%)\n"
        details += f"{'Total':.<35} {total_oils/28.3495:>8.2f}oz\n\n"
        
        details += "LYE SOLUTION:\n"
        details += "-" * 60 + "\n"
        details += f"{'Sodium Hydroxide (NaOH)':.<35} {recipe.lye_amount/28.3495:>8.2f}oz\n"
        details += f"{'Water':.<35} {recipe.water_amount/28.3495:>8.2f}oz\n"
        details += f"{'Lye Concentration':.<35} {recipe.lye_concentration:>7.1f}%\n"
        details += f"{'Superfat':.<35} {recipe.superfat:>7.1f}%\n\n"
        
        if recipe.fragrance_amount > 0:
            details += "ADDITIVES:\n"
            details += "-" * 60 + "\n"
            details += f"{'Fragrance/Essential Oil':.<35} {recipe.fragrance_amount/28.3495:>8.2f}oz\n\n"
        
        if recipe.properties:
            details += "SOAP PROPERTIES:\n"
            details += "-" * 60 + "\n"
            for prop, value in recipe.properties.items():
                details += f"{prop.capitalize():.<35} {value:>7.1f}\n"
            details += "\n"
        
        if recipe.notes:
            details += "NOTES:\n"
            details += "-" * 60 + "\n"
            details += recipe.notes + "\n"
        
        self.recipe_details_text.insert(1.0, details)
    
    def load_selected_recipe(self):
        """Load selected recipe into calculator."""
        selection = self.recipes_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a recipe to load.")
            return
        
        item = self.recipes_tree.item(selection[0])
        idx = int(item['text']) - 1
        
        recipe = self.recipe_manager.get_recipe(idx)
        if recipe:
            # Load recipe into calculator
            self.recipe_name_var.set(recipe.name)
            self.superfat_var.set(str(recipe.superfat))
            self.lye_conc_var.set(str(recipe.lye_concentration))
            self.fragrance_var.set(str(recipe.fragrance_percent))
            
            # Clear existing oil values
            for var, _ in self.oil_entries.values():
                var.set("0")
            
            # Set oil values (convert back to ounces)
            for oil_name, weight_grams in recipe.oils.items():
                if oil_name in self.oil_entries:
                    weight_oz = weight_grams / 28.3495
                    var, _ = self.oil_entries[oil_name]
                    var.set(f"{weight_oz:.2f}")
            
            # Clear and load modifiers
            for enabled_var, amount_var, entry in self.modifier_entries.values():
                enabled_var.set(False)
                amount_var.set("0")
                entry.config(state='disabled')
            
            if hasattr(recipe, 'modifiers') and recipe.modifiers:
                total_oils = sum(recipe.oils.values())
                for mod_name, amount_grams in recipe.modifiers.items():
                    if mod_name in self.modifier_entries:
                        enabled_var, amount_var, entry = self.modifier_entries[mod_name]
                        modifier_info = self.chemistry.get_modifier_info(mod_name)
                        usage_rate_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                        
                        enabled_var.set(True)
                        entry.config(state='normal')
                        
                        if usage_rate_type == 'percent_of_oils':
                            # Convert back to percentage
                            percent = (amount_grams / total_oils) * 100
                            amount_var.set(f"{percent:.2f}")
                        else:
                            amount_var.set(f"{amount_grams:.2f}")
            
            messagebox.showinfo("Recipe Loaded", f"Recipe '{recipe.name}' loaded into calculator.")
    
    def delete_selected_recipe(self):
        """Delete the selected recipe."""
        selection = self.recipes_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a recipe to delete.")
            return
        
        item = self.recipes_tree.item(selection[0])
        idx = int(item['text']) - 1
        
        recipe = self.recipe_manager.get_recipe(idx)
        if recipe:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{recipe.name}'?"):
                self.recipe_manager.delete_recipe(idx)
                self.refresh_recipes_list()
                self.recipe_details_text.delete(1.0, tk.END)
                messagebox.showinfo("Deleted", "Recipe deleted successfully.")
    
    def export_current_recipe_to_pdf(self):
        """Export the current recipe from calculator to PDF."""
        try:
            # Get oil weights (convert from ounces to grams)
            oil_weights = {}
            for oil_name, (var, _) in self.oil_entries.items():
                weight_oz = float(var.get() or 0)
                if weight_oz > 0:
                    oil_weights[oil_name] = weight_oz * 28.3495
            
            if not oil_weights:
                messagebox.showwarning("No Recipe", "Please enter oil weights and calculate before exporting.")
                return
            
            # Get modifiers
            modifiers = {}
            total_oils = sum(oil_weights.values())
            for modifier_name, (enabled_var, amount_var, _) in self.modifier_entries.items():
                if enabled_var.get():
                    modifier_info = self.chemistry.get_modifier_info(modifier_name)
                    usage_rate_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                    
                    if usage_rate_type == 'percent_of_oils':
                        percent = float(amount_var.get() or 0)
                        modifiers[modifier_name] = total_oils * percent / 100
                    else:
                        modifiers[modifier_name] = float(amount_var.get() or 0)
            
            # Create temporary recipe
            recipe = Recipe(
                name=self.recipe_name_var.get(),
                oils=oil_weights,
                superfat=float(self.superfat_var.get()),
                lye_concentration=float(self.lye_conc_var.get()),
                fragrance_percent=float(self.fragrance_var.get()),
                modifiers=modifiers
            )
            
            # Calculate values
            recipe.lye_amount, recipe.lye_adjustment = self.chemistry.calculate_lye_amount(
                oil_weights, recipe.superfat, modifiers=modifiers
            )
            recipe.water_amount = self.chemistry.calculate_water_amount(
                recipe.lye_amount + recipe.lye_adjustment, recipe.lye_concentration
            )
            recipe.fragrance_amount = self.chemistry.calculate_fragrance_amount(total_oils, recipe.fragrance_percent)
            recipe.properties = self.chemistry.calculate_soap_properties(oil_weights)
            recipe.fatty_acids = self.chemistry.calculate_fatty_acid_profile(oil_weights)
            
            # Export
            self.export_recipe_to_pdf(recipe)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export recipe: {str(e)}")
    
    def export_selected_recipe_to_pdf(self):
        """Export the selected saved recipe to PDF."""
        selection = self.recipes_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a recipe to export.")
            return
        
        item = self.recipes_tree.item(selection[0])
        idx = int(item['text']) - 1
        
        recipe = self.recipe_manager.get_recipe(idx)
        if recipe:
            self.export_recipe_to_pdf(recipe)
    
    def export_recipe_to_pdf(self, recipe):
        """Export a recipe to PDF with helpful tips."""
        self.export_recipe_to_pdf_existing_file(recipe, None, None)
    
    def export_recipe_to_pdf_existing_file(self, recipe, filename=None, colorant_info=None):
        """Export a recipe to PDF with optional colorant info and custom filename."""
        # Get user's desktop as default location (more reliable than Documents)
        if not filename:
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
            # Ensure the directory exists
            output_dir = os.path.dirname(filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            doc = SimpleDocTemplate(filename, pagesize=letter,
                                   topMargin=0.75*inch, bottomMargin=0.75*inch,
                                   leftMargin=0.75*inch, rightMargin=0.75*inch)
            
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Title
            story.append(Paragraph(f"<b>{recipe.name}</b>", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Recipe info
            info_text = f"Created: {datetime.fromisoformat(recipe.created_date).strftime('%B %d, %Y')}"
            
            # Add soap type if available
            if hasattr(recipe, 'soap_type') and recipe.soap_type:
                info_text += f" | Base Type: {recipe.soap_type}"
            
            story.append(Paragraph(info_text, styles['Normal']))
            
            # Add scent profile if available
            if hasattr(recipe, 'scent_info') and recipe.scent_info:
                scent_text = f"<b>Scent Profile:</b> {recipe.scent_info['name']}"
                story.append(Paragraph(scent_text, styles['Normal']))
                scent_recipe = f"<i>Recipe: {recipe.scent_info['recipe']}</i>"
                story.append(Paragraph(scent_recipe, styles['Normal']))
                scent_notes = f"<i>{recipe.scent_info['notes']}</i>"
                story.append(Paragraph(scent_notes, styles['Normal']))
            
            story.append(Spacer(1, 0.3*inch))
            
            # OILS TABLE
            story.append(Paragraph("<b>OILS</b>", heading_style))
            oil_data = [['Oil Name', 'Amount (oz)', 'Percentage']]
            total_oils = sum(recipe.oils.values())
            for oil, weight in sorted(recipe.oils.items()):
                percentage = (weight / total_oils) * 100
                weight_oz = weight / 28.3495
                oil_data.append([oil, f"{weight_oz:.2f} oz", f"{percentage:.1f}%"])
            oil_data.append(['<b>Total Oils</b>', f"<b>{total_oils/28.3495:.2f} oz</b>", '<b>100%</b>'])
            
            oil_table = Table(oil_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            oil_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(oil_table)
            story.append(Spacer(1, 0.3*inch))
            
            # LYE SOLUTION TABLE
            story.append(Paragraph("<b>LYE SOLUTION</b>", heading_style))
            lye_data = [
                ['Ingredient', 'Amount (oz)', 'Notes']
            ]
            
            # Add base lye amount
            total_lye = recipe.lye_amount
            lye_adjustment = getattr(recipe, 'lye_adjustment', 0.0)
            
            if lye_adjustment > 0:
                lye_data.append(['Sodium Hydroxide (base)', f"{recipe.lye_amount/28.3495:.2f} oz", 'For saponification'])
                lye_data.append(['+ Extra NaOH for modifiers', f"{lye_adjustment/28.3495:.2f} oz", 'For citric acid/modifiers'])
                lye_data.append(['= Total Sodium Hydroxide', f"{(recipe.lye_amount + lye_adjustment)/28.3495:.2f} oz", 'CAUSTIC - Handle with care!'])
                total_lye = recipe.lye_amount + lye_adjustment
            else:
                lye_data.append(['Sodium Hydroxide (NaOH)', f"{recipe.lye_amount/28.3495:.2f} oz", 'Caustic - Handle with care'])
            
            lye_data.extend([
                ['Water', f"{recipe.water_amount/28.3495:.2f} oz", 'Distilled water recommended'],
                ['Lye Concentration', f"{recipe.lye_concentration:.1f}%", ''],
                ['Superfat', f"{recipe.superfat:.1f}%", 'For skin-friendly soap']
            ])
            
            lye_table = Table(lye_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
            lye_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(lye_table)
            story.append(Spacer(1, 0.3*inch))
            
            # ADDITIVES
            has_additives = recipe.fragrance_amount > 0 or (hasattr(recipe, 'modifiers') and recipe.modifiers)
            
            # Debug output
            print(f"DEBUG: has_additives={has_additives}")
            print(f"DEBUG: fragrance_amount={recipe.fragrance_amount}")
            print(f"DEBUG: hasattr modifiers={hasattr(recipe, 'modifiers')}")
            if hasattr(recipe, 'modifiers'):
                print(f"DEBUG: recipe.modifiers={recipe.modifiers}")
            
            if has_additives:
                story.append(Paragraph("<b>ADDITIVES</b>", heading_style))
                additive_data = [
                    ['Additive', 'Amount', 'When to Add']
                ]
                
                # Add fragrance
                if recipe.fragrance_amount > 0:
                    additive_data.append([
                        'Fragrance/Essential Oil', 
                        f"{recipe.fragrance_amount/28.3495:.2f} oz", 
                        'At trace (after blending)'
                    ])
                
                # Add modifiers
                if hasattr(recipe, 'modifiers') and recipe.modifiers:
                    for modifier_name, amount_grams in recipe.modifiers.items():
                        modifier_info = self.chemistry.get_modifier_info(modifier_name)
                        
                        # Format amount based on type
                        usage_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                        if usage_type == 'percent_of_oils':
                            amount_str = f"{amount_grams:.1f}g ({amount_grams/28.3495:.2f}oz)"
                        elif usage_type == 'tablespoons_per_pound':
                            amount_str = f"{amount_grams:.1f} tbsp"
                        else:
                            amount_str = f"{amount_grams:.1f}g"
                        
                        # Determine when to add
                        dissolve_in = modifier_info.get('dissolve_in', '')
                        if 'lye' in dissolve_in.lower():
                            when = 'Dissolve in lye water'
                        else:
                            when = 'At trace'
                        
                        additive_data.append([modifier_name, amount_str, when])
                
                additive_table = Table(additive_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
                additive_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                story.append(additive_table)
                story.append(Spacer(1, 0.3*inch))
            
            # NATURAL COLORANTS (if provided)
            print(f"DEBUG PDF: colorant_info = {colorant_info}")
            if colorant_info:
                print(f"DEBUG PDF: colorant_info.get('colorants') = {colorant_info.get('colorants')}")
            
            if colorant_info and colorant_info.get('colorants'):
                print(f"DEBUG PDF: Adding colorant section to PDF")
                story.append(Paragraph("<b>NATURAL COLORANTS</b>", heading_style))
                story.append(Paragraph(f"<i>Target Color: {colorant_info['color_name']}</i>", styles['Normal']))
                
                # Colorant tips with detailed instructions
                story.append(Paragraph("<b><i>How to Add Colorants:</i></b>", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                colorant_instructions = [
                    ("<b>1. Prepare Ahead:</b>", "Mix each colorant with 1-2 tablespoons of your soap oils (from the recipe) in a small container. Stir until no clumps remain."),
                    ("<b>2. When to Add:</b>", "Add colorants at light to medium trace, AFTER adding fragrance. If swirling, work at a lighter trace."),
                    ("<b>3. Mixing In:</b>", "Pour the pre-mixed colorant into your soap batter and use your stick blender or whisk to blend thoroughly. Check for streaks."),
                    ("<b>4. For Multiple Colors:</b>", "Divide your traced soap into separate containers, add different colorants to each, then layer or swirl."),
                    ("<b>5. Natural Color Notes:</b>", "Clays, oxides, and micas: Use as listed. Infused oils: Substitute part of your recipe oils. Powders (spirulina, turmeric): Start with half the recommended amount as they're potent."),
                    ("<b>6. Important:</b>", "Natural colors may fade, morph, or shift over time (especially purples/blues). This is normal! Test in small batches first.")
                ]
                
                for instruction_title, instruction_text in colorant_instructions:
                    story.append(Paragraph(f"{instruction_title} {instruction_text}", styles['Normal']))
                    story.append(Spacer(1, 0.08*inch))
                story.append(Spacer(1, 0.2*inch))
            
            # SOAP PROPERTIES
            if recipe.properties:
                story.append(Paragraph("<b>SOAP PROPERTIES</b>", heading_style))
                props_data = [['Property', 'Value', 'Recommended Range']]
                ranges = self.settings.get('recommended_ranges', {})
                
                for prop, value in sorted(recipe.properties.items()):
                    range_val = ranges.get(prop, ['N/A', 'N/A'])
                    if isinstance(range_val, list) and len(range_val) == 2:
                        range_str = f"{range_val[0]} - {range_val[1]}"
                    else:
                        range_str = "N/A"
                    props_data.append([prop.capitalize(), f"{value:.1f}", range_str])
                
                props_table = Table(props_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
                props_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                story.append(props_table)
                story.append(Spacer(1, 0.3*inch))
            
            # NEW PAGE FOR INSTRUCTIONS
            story.append(PageBreak())
            
            # SOAP MAKING INSTRUCTIONS
            story.append(Paragraph("<b>SOAP MAKING INSTRUCTIONS</b>", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            instructions = [
                ("<b>1. SAFETY FIRST</b>", [
                    "Wear safety goggles and gloves at all times",
                    "Work in a well-ventilated area",
                    "Keep vinegar nearby to neutralize lye spills",
                    "Never add water to lye - always add lye to water",
                    "Keep children and pets away from your workspace"
                ]),
                ("<b>2. PREPARE YOUR LYE SOLUTION</b>", self._get_lye_instructions(recipe)),
                ("<b>3. PREPARE YOUR OILS</b>", [
                    "Measure and combine all oils in a large stainless steel or heat-proof plastic container",
                    "If using solid oils/fats, melt them first",
                    "Heat oils to approximately 100-110°F",
                    "Use a thermometer to check temperatures"
                ]),
                ("<b>4. COMBINE LYE AND OILS</b>", [
                    "When both lye solution and oils are at 100-110°F, slowly pour lye into oils",
                    "Mix with an immersion (stick) blender in short bursts",
                    "Alternate blending with stirring to prevent air bubbles",
                    "Continue until mixture reaches 'trace' (consistency of thin pudding)"
                ]),
                ("<b>5. ADD FRAGRANCE AND ADDITIVES</b>", self._get_additive_instructions(recipe)),
                ("<b>6. POUR AND CURE</b>", [
                    "Pour soap mixture into molds",
                    "Tap molds gently to release air bubbles",
                    "Cover and insulate for 24 hours",
                    "Unmold after 24-48 hours when firm",
                    "Cut into bars if using a loaf mold",
                    "Cure for 4-6 weeks in a cool, dry place with good air circulation",
                    "Turn bars weekly during curing"
                ])
            ]
            
            for section_title, steps in instructions:
                story.append(Paragraph(section_title, heading_style))
                for step in steps:
                    story.append(Paragraph(f"• {step}", styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
                story.append(Spacer(1, 0.15*inch))
            
            # HELPFUL TIPS
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>HELPFUL TIPS</b>", heading_style))
            
            tips = [
                "<b>Temperature Matters:</b> Keep oils and lye solution within 10°F of each other for best results",
                "<b>Trace Stages:</b> Light trace for swirls, medium trace for most soaps, thick trace for textured tops",
                "<b>Testing pH:</b> After curing, test pH with strips. Safe soap should be 9-10 pH",
                "<b>Color Issues:</b> High temperatures can cause discoloration. Keep below 120°F when mixing",
                "<b>Scent Retention:</b> Essential oils fade faster than fragrance oils. Use at 3% of oil weight",
                "<b>Soft Soap Fix:</b> Longer curing time and harder oils (coconut, palm) create harder bars",
                f"<b>Your Recipe Notes:</b> Hardness={recipe.properties.get('hardness', 0):.0f}, " +
                f"Conditioning={recipe.properties.get('conditioning', 0):.0f}, " +
                f"Cleansing={recipe.properties.get('cleansing', 0):.0f}"
            ]
            
            for tip in tips:
                story.append(Paragraph(f"✓ {tip}", styles['Normal']))
                story.append(Spacer(1, 0.08*inch))
            
            # Build PDF
            doc.build(story)
            messagebox.showinfo("Success", f"Recipe exported successfully to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create PDF: {str(e)}")
    
    def _get_lye_instructions(self, recipe):
        """Generate lye preparation instructions based on recipe."""
        instructions = [
            f"Measure {recipe.water_amount/28.3495:.2f} oz of distilled water in a heat-safe container"
        ]
        
        lye_adjustment = getattr(recipe, 'lye_adjustment', 0.0)
        total_lye = recipe.lye_amount + lye_adjustment
        
        if lye_adjustment > 0:
            instructions.append(f"Slowly add {total_lye/28.3495:.2f} oz of sodium hydroxide to the water while stirring")
            instructions.append(f"(This includes {lye_adjustment/28.3495:.2f} oz extra for citric acid/modifiers)")
        else:
            instructions.append(f"Slowly add {recipe.lye_amount/28.3495:.2f} oz of sodium hydroxide to the water while stirring")
        
        instructions.extend([
            "ALWAYS add lye to water, NEVER water to lye!",
            "The solution will heat up to 180-200°F - this is normal",
            "Stir until all lye is dissolved and solution is clear",
            "Set aside and allow to cool to 100-110°F",
            "Work in a sink or on a heat-proof surface"
        ])
        
        return instructions
    
    def _get_additive_instructions(self, recipe):
        """Generate instructions for adding fragrance and modifiers."""
        instructions = []
        
        # Instructions for modifiers that go in lye water
        if hasattr(recipe, 'modifiers') and recipe.modifiers:
            lye_modifiers = []
            trace_modifiers = []
            
            for modifier_name in recipe.modifiers.keys():
                modifier_info = self.chemistry.get_modifier_info(modifier_name)
                dissolve_in = modifier_info.get('dissolve_in', '')
                
                if 'lye' in dissolve_in.lower():
                    lye_modifiers.append(modifier_name)
                else:
                    trace_modifiers.append(modifier_name)
            
            if lye_modifiers:
                instructions.append(f"NOTE: {', '.join(lye_modifiers)} should have been dissolved in lye water earlier")
        
        # Main trace instructions
        if recipe.fragrance_amount > 0:
            instructions.append(f"Once at trace, add {recipe.fragrance_amount/28.3495:.2f} oz of fragrance or essential oils")
            instructions.append("Mix thoroughly but quickly - some fragrances accelerate trace")
        
        # Other modifiers at trace
        if hasattr(recipe, 'modifiers') and recipe.modifiers:
            for modifier_name, amount in recipe.modifiers.items():
                modifier_info = self.chemistry.get_modifier_info(modifier_name)
                dissolve_in = modifier_info.get('dissolve_in', '')
                
                if 'lye' not in dissolve_in.lower():
                    usage_type = modifier_info.get('usage_rate_type', 'percent_of_oils')
                    if usage_type == 'percent_of_oils':
                        amount_str = f"{amount:.1f}g ({amount/28.3495:.2f}oz)"
                    else:
                        amount_str = f"{amount:.1f}g"
                    instructions.append(f"Add {amount_str} of {modifier_name} and blend well")
        
        if not instructions:
            instructions.append("No additives in this recipe")
        
        return instructions
    
    def _calculate_colorant_amount(self, usage_rate_str, batch_size_lbs):
        """
        Calculate the actual amount of colorant needed for a specific batch size.
        
        Args:
            usage_rate_str: String like "1 tsp per pound of oils" or "1-2 tsp per pound"
            batch_size_lbs: Batch size in pounds
            
        Returns:
            String with calculated amount
        """
        import re
        
        # Parse the usage rate string
        # Examples: "1 tsp per pound", "1-2 tsp per pound", "1/4-1/2 tsp per pound", "1-3% of oils"
        
        # Check for percentage-based
        percent_match = re.search(r'([\d./-]+)\s*%', usage_rate_str)
        if percent_match:
            # Return as-is since percentages are already relative
            return f"Use {usage_rate_str}"
        
        # Check for tsp/tbsp per pound
        amount_match = re.search(r'([\d./-]+)\s*(tsp|tbsp|teaspoon|tablespoon)', usage_rate_str, re.IGNORECASE)
        if amount_match:
            amount_str = amount_match.group(1)
            unit = amount_match.group(2).lower()
            
            # Parse amount (handle fractions and ranges)
            if '-' in amount_str:
                # Range like "1-2" or "1/4-1/2"
                parts = amount_str.split('-')
                min_val = self._parse_fraction(parts[0])
                max_val = self._parse_fraction(parts[1])
                mid_val = (min_val + max_val) / 2
                
                min_batch = min_val * batch_size_lbs
                max_batch = max_val * batch_size_lbs
                
                if 'tsp' in unit or 'teaspoon' in unit:
                    return f"{min_batch:.2f}-{max_batch:.2f} tsp"
                else:
                    return f"{min_batch:.2f}-{max_batch:.2f} tbsp"
            else:
                # Single value
                val = self._parse_fraction(amount_str)
                batch_amount = val * batch_size_lbs
                
                if 'tsp' in unit or 'teaspoon' in unit:
                    return f"{batch_amount:.2f} tsp"
                else:
                    return f"{batch_amount:.2f} tbsp"
        
        # If we can't parse it, return the original with batch size note
        return f"See rate ({batch_size_lbs:.1f} lb batch)"
    
    def _parse_fraction(self, fraction_str):
        """Parse a fraction string like '1/4' or '1.5' to a float."""
        fraction_str = fraction_str.strip()
        if '/' in fraction_str:
            parts = fraction_str.split('/')
            return float(parts[0]) / float(parts[1])
        return float(fraction_str)
    
    def create_oils_tab(self, parent):
        """Create oil properties database view."""
        # TODO: Implement oil database view
        label = ttk.Label(parent, text="Oil Properties Database (Coming Soon)", 
                         font=('Arial', 14))
        label.pack(pady=20)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = SoapMakerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
