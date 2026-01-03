# Soap Making Application

A desktop application for creating scientifically accurate soap recipes based on chemistry principles.

## Features

- **Chemistry-Based Calculations**: Accurate saponification values for different oils
- **Recipe Manager**: Create, save, and modify soap recipes
- **Quality Predictions**: Analyze hardness, cleansing, conditioning, and other soap properties
- **Lye Calculator**: Automatic lye calculation based on oils and water content
- **Fragrance Calculator**: Proper essential oil/fragrance calculations to prevent scent fade

## Project Structure

```
SoapApp/
├── src/
│   ├── main.py              # Application entry point
│   ├── gui/                 # GUI components
│   ├── chemistry/           # Chemistry calculations
│   └── models/              # Data models
├── data/
│   ├── oils.json           # Oil properties database
│   └── recipes.json        # Saved recipes
└── config/
    └── settings.json       # Application settings
```

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python src/main.py
```

## Chemistry Principles

The application uses:
- SAP (Saponification) values for accurate lye calculations
- Fatty acid profiles for property predictions
- INS (Iodine Number Scale) for hardness calculations
- Proper superfat percentages for skin-friendly soap
