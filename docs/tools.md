# Clinical & Metric Tools

ClinicRAG features 16 registered clinical and health metric tools.

## 1. Pharmacology & Medication Intelligence
- **`medicine_lookup`**: Fetches full SPL drug label sections from 3,330+ local FDA DailyMed XML files with OpenFDA live API fallback.
- **`drug_interactions`**: Checks cross-medication interactions with severity ratings (Major, Moderate, Minor) and clinical mechanisms.
- **`medicine_dosage`**: Queries verified dosage guidelines, packaging, and administration precautions.

## 2. Clinical Guidance & Symptom RAG
- **`symptom_checker`**: Vector search over MedlinePlus and WHO literature for symptoms, home care, and warning signs.
- **`disease_lookup`**: Detailed disease pathophysiology, risk factors, and clinical treatment guidelines.
- **`nutrition_lookup`**: Dietary recommendations, macronutrient balance, and chronic disease nutritional protocols.
- **`pregnancy_lookup`**: Antenatal care milestones, trimester-specific guidance, and contraindications.

## 3. Emergency Care & Triage
- **`emergency_first_aid_guide`**: Step-by-step protocol for CPR, burns, bleeding, choking (Heimlich), fractures, and poisoning.
- **`emergency_triage`**: Immediate clinical red-flag severity scoring.

## 4. Health Metric Calculators & Converters
- **`bmi_calculator`**: Calculates Body Mass Index (BMI) with WHO clinical weight classification.
- **`bmr_calculator`**: Calculates Basal Metabolic Rate via Mifflin-St Jeor formula.
- **`calorie_calculator`**: Estimates Total Daily Energy Expenditure (TDEE) from activity multipliers.
- **`water_calculator`**: Calculates recommended hydration based on body mass.
- **`unit_converter`**: Accurate clinical conversion for blood glucose (mg/dL <-> mmol/L), temperature (F <-> C), weight, and height.
