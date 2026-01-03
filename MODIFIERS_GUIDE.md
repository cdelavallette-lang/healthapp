# Modifiers Feature - Quick Start Guide

## Overview
The SoapApp now supports adding modifiers/additives to your soap recipes! These include citric acid, sodium lactate, clays, sugars, and more.

## What's New

### 1. New Modifier Section in Calculator
- Located below the Parameters section in the Recipe Calculator tab
- Checkbox-based interface to enable/disable each modifier
- Info buttons (?) to view detailed information about each modifier
- Automatic calculation of recommended amounts

### 2. Supported Modifiers

#### **Citric Acid** (Chelating Agent)
- **Usage**: 0.5-3% (typical 1%)
- **Effects**: 
  - Lowers pH for milder soap
  - Chelates minerals in hard water
  - Improves lather in hard water
- **Important**: Automatically adds extra lye (6g NaOH per 10g citric acid)

#### **Sodium Lactate** (Hardener)
- **Usage**: 1-3% (typical 2%)
- **Effects**: Hardens bars, helps with unmolding

#### **Sugar** (Lather Booster)
- **Usage**: 1-5% (typical 3%)
- **Effects**: Increases lather and bubbles
- **Note**: Dissolve in lye water before use

#### **Salt** (Hardener)
- **Usage**: 1-100% (typical 3%)
- **Effects**: Creates harder bar, reduces lather at high amounts

#### **Kaolin Clay** (Additive)
- **Usage**: 0.5-2% (typical 1%)
- **Effects**: Adds slip, anchors fragrance, lightens colors

#### **Bentonite Clay** (Additive)
- **Usage**: 0.5-2% (typical 1%)
- **Effects**: Detoxifying, adds grey-green color

#### **Colloidal Oatmeal** (Additive)
- **Usage**: 0.5-3% (typical 1%)
- **Effects**: Soothing, gentle exfoliation

#### **Silk Amino Acids** (Luxury)
- **Usage**: 0.25-2% (typical 0.5%)
- **Effects**: Adds luxury feel and silkiness

#### **Vitamin E Oil** (Antioxidant)
- **Usage**: 0.1-1% (typical 0.5%)
- **Effects**: Extends shelf life, moisturizing

## How to Use

### In the Recipe Calculator:
1. Enter your oils and parameters as usual
2. Scroll down to the "Modifiers / Additives" section
3. Check the box next to the modifier you want to add
4. The entry field becomes active with a suggested amount (in grams or tbsp)
5. Adjust the amount if desired
6. Click the "?" button for detailed information about any modifier
7. Click "Calculate" - the lye adjustment for citric acid is automatic!

### In Results:
- Extra lye for modifiers (if any) is shown separately
- Total lye amount includes the adjustment
- Modifiers are listed in the Additives section

### Saving Recipes:
- Modifiers are automatically saved with your recipe
- When you load a saved recipe, modifiers are restored

### Effects on Color and Scent:
- **Citric Acid**: Minimal effect - may slightly lighten natural colorants
- **Clays**: Can add color (white for kaolin, grey-green for bentonite)
- **Oatmeal**: Adds tan/beige color with specks
- Most other modifiers have no effect on color or scent

## Technical Details

### Lye Adjustment
Citric acid reacts with lye (sodium hydroxide), so extra lye must be added:
- **Formula**: 6g NaOH per 10g citric acid (0.6 factor)
- This is calculated automatically by the app
- The adjustment is added to your base lye amount

### Data File
Modifiers are stored in `data/modifiers.json` with detailed information including:
- Category (chelating agent, hardener, additive, etc.)
- Typical and range of usage percentages
- Lye adjustment factors
- Effects on color, scent, lather, hardness, and skin feel
- Usage instructions

## Tips
1. Start with typical usage amounts and adjust as you gain experience
2. Read the modifier info (? button) before using
3. For citric acid, the app handles the lye adjustment automatically - no manual calculation needed!
4. Some modifiers (clays, silk) may need special preparation - check the info
5. When combining multiple modifiers, consider their cumulative effects

## Example Recipe with Citric Acid
```
Oils:
- Coconut Oil: 7oz
- Olive Oil: 14oz  
- Palm Oil: 7oz

Parameters:
- Superfat: 5%
- Lye Concentration: 33%

Modifiers:
☑ Citric Acid: 8g (1% of oils)

Results:
- Base Lye: 112.1g (3.95oz)
- Extra for citric acid: +4.8g (0.17oz)
- Total Lye: 116.9g (4.12oz)
- Water: 237.1g (8.36oz)
```

The app automatically calculated that 8g of citric acid requires an additional 4.8g of lye!

## Troubleshooting
- If modifiers don't appear, ensure `data/modifiers.json` exists
- The percentage field is based on oil weight (percent_of_oils)
- Some modifiers use tablespoons (tbsp) instead of grams
- Check the info popup for specific usage instructions
