import json
import requests
import streamlit as st
from typing import Dict, Any, Union, Optional, List
from langchain_core.tools import tool
from src.config import config
from src.utils import load_json
from src.logger import logger
from src.constants import EMERGENCY_SIGNS
from src.fda_parser import get_fda_drug_info

# Lazy loaders for database
def _get_medicines_db() -> Dict[str, Any]:
    return load_json(config.MEDICINES_DB_PATH)

def _get_interactions_db() -> Dict[str, Any]:
    return load_json(config.INTERACTIONS_DB_PATH)

_retriever = None
def _get_retriever():
    global _retriever
    if _retriever is None:
        from src.retriever import MedicalRetriever
        _retriever = MedicalRetriever()
    return _retriever

def _query_openfda(medicine_name: str) -> Optional[dict]:
    """Helper to query the live OpenFDA API with short timeout."""
    try:
        med_clean = medicine_name.strip().replace(" ", "+")
        url = f'https://api.fda.gov/drug/label.json?search=openfda.brand_name:"{med_clean}"+openfda.generic_name:"{med_clean}"&limit=1'
        logger.info(f"Querying OpenFDA API: {url}")
        res = requests.get(url, timeout=2.0)
        
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if results:
                label = results[0]
                
                def get_first_or_join(field_key) -> str:
                    val = label.get(field_key, "")
                    if isinstance(val, list):
                        return "\n".join(val)
                    return str(val)
                
                return {
                    "name": get_first_or_join("openfda").split("\n")[0] if "openfda" in label else medicine_name,
                    "generic": get_first_or_join("openfda").split("\n")[0] if "openfda" in label else "N/A",
                    "uses": get_first_or_join("purpose") or get_first_or_join("indications_and_usage") or "N/A",
                    "side_effects": get_first_or_join("adverse_reactions") or "N/A",
                    "warnings": get_first_or_join("warnings") or get_first_or_join("warnings_and_precautions") or "N/A",
                    "storage": get_first_or_join("how_supplied") or get_first_or_join("storage_and_handling") or "N/A",
                    "interactions": get_first_or_join("drug_interactions") or "N/A",
                    "source": "OpenFDA Live API"
                }
    except Exception as e:
        logger.warning(f"OpenFDA API call failed/timed out: {e}")
    return None

# --- 1. medical_rag ---
@tool
def medical_rag(query: str) -> str:
    """Queries the persistent medical knowledge base for details on symptoms, diseases, healthcare FAQs, lifestyles, nutrition, or general health concerns."""
    logger.info(f"Tool Call - Knowledge Retriever: {query}")
    retriever = _get_retriever()
    docs = retriever.retrieve(query)
    
    if not docs:
        return "No matching records found in the medical knowledge base."
    
    try:
        st.session_state["last_retrieved_docs"] = docs
    except Exception as e:
        logger.warning(f"Failed to save retrieved docs to session state: {e}")
        
    formatted = []
    for doc in docs:
        conf_str = f" [Confidence: {doc.metadata['confidence_score']:.1%}]" if "confidence_score" in doc.metadata else ""
        formatted.append(
            f"Source: {doc.metadata.get('source_name', 'Unknown')}{conf_str}\n"
            f"Category: {doc.metadata.get('category', 'General')}\n"
            f"Section: {doc.metadata.get('section', 'General')}\n"
            f"Content: {doc.page_content}"
        )
    return "\n\n".join(formatted)

# --- 2. medicine_lookup ---
@tool
def medicine_lookup(medicine_name: str) -> str:
    """Retrieves brand name, generic name, usage, side effects, warnings, dosage, and storage details for a given medicine name."""
    logger.info(f"Tool Call - Medicine Info: {medicine_name}")
    
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("medicine_lookup")
        
    # 1. Try local FDA SPL XML database first
    fda_info = get_fda_drug_info(medicine_name)
    if fda_info:
        st.session_state["active_medicine_badge"] = "FDA DailyMed Label"
        return (
            f"### Official FDA Drug Label Information ({fda_info['category'].upper()})\n"
            f"**Brand/Product Name**: {fda_info['name']}\n"
            f"**Generic Name**: {fda_info['generic']}\n\n"
            f"**Indications & Uses**:\n{fda_info['uses']}\n\n"
            f"**Warnings & Precautions**:\n{fda_info['warnings']}\n\n"
            f"**Adverse Reactions & Side Effects**:\n{fda_info['side_effects']}\n\n"
            f"**Drug Interactions**:\n{fda_info['interactions']}\n\n"
            f"**Dosage & Storage**:\n{fda_info['storage']}\n\n"
            f"*(Source: FDA Structured Product Labeling Database)*"
        )
        
    # 2. Try live OpenFDA API as backup
    openfda_info = _query_openfda(medicine_name)
    if openfda_info:
        st.session_state["active_medicine_badge"] = "OpenFDA Live API"
        return (
            f"### Live OpenFDA API Drug Label Information\n"
            f"**Brand Name**: {openfda_info['name']}\n"
            f"**Generic Name**: {openfda_info['generic']}\n\n"
            f"**Indications & Uses**:\n{openfda_info['uses']}\n\n"
            f"**Warnings & Precautions**:\n{openfda_info['warnings']}\n\n"
            f"**Adverse Reactions & Side Effects**:\n{openfda_info['side_effects']}\n\n"
            f"**Drug Interactions**:\n{openfda_info['interactions']}\n\n"
            f"**Storage Details**:\n{openfda_info['storage']}\n\n"
            f"*(Source: OpenFDA Live Database API)*"
        )
        
    # 3. Fallback to static verified database
    db = _get_medicines_db()
    med_key = medicine_name.strip().lower()
    if med_key in db:
        med = db[med_key]
        st.session_state["active_medicine_badge"] = "Verified Database"
        return (
            f"**Medicine Name**: {med.get('name')}\n"
            f"**Generic Name**: {med.get('generic')}\n"
            f"**Uses**: {med.get('uses')}\n"
            f"**Common Side Effects**: {med.get('side_effects')}\n"
            f"**Warnings**: {med.get('warnings')}\n"
            f"**Storage**: {med.get('storage')}\n"
            f"**Interactions**: {med.get('interactions')}"
        )
        
    return (
        f"Sorry, I do not have pre-verified pharmaceutical information for '{medicine_name}' in my local database, parsed FDA labels, or OpenFDA API. "
        "Please consult a certified pharmacist or physician for accurate information regarding this medicine."
    )

# --- 3. drug_interactions ---
@tool
def drug_interactions(medicine_a: str, medicine_b: str) -> str:
    """Checks if there are any known dangerous interactions when combining Medicine A and Medicine B."""
    logger.info(f"Tool Call - Drug Interaction Checker: {medicine_a} + {medicine_b}")
    db = _get_interactions_db()
    
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("drug_interactions")
        
    med_a = medicine_a.strip().lower()
    med_b = medicine_b.strip().lower()
    
    # 1. Try static database lookup first
    key1 = f"{med_a}+{med_b}"
    key2 = f"{med_b}+{med_a}"
    
    interaction = db.get(key1) or db.get(key2)
    
    if interaction:
        return (
            f"### Drug Interaction Warning: {interaction['severity']}\n"
            f"**Meds involved**: {interaction['drugs'][0]} and {interaction['drugs'][1]}\n"
            f"**Severity**: {interaction['severity']}\n"
            f"**Mechanism**: {interaction['mechanism']}\n"
            f"**Recommendation**: {interaction['recommendation']}"
        )
        
    # 2. Dynamic check using local FDA XML database
    info_a = get_fda_drug_info(med_a)
    info_b = get_fda_drug_info(med_b)
    
    warnings = []
    
    if info_a and info_a.get("interactions") and info_a["interactions"] != "Refer to professional clinical consultation.":
        interactions_text = info_a["interactions"].lower()
        if med_b in interactions_text or (info_b and info_b["name"].lower() in interactions_text):
            warnings.append(
                f"Based on the official FDA label for **{info_a['name']}**:\n"
                f"> {info_a['interactions']}"
            )
            
    if info_b and info_b.get("interactions") and info_b["interactions"] != "Refer to professional clinical consultation.":
        interactions_text = info_b["interactions"].lower()
        if med_a in interactions_text or (info_a and info_a["name"].lower() in interactions_text):
            warnings.append(
                f"Based on the official FDA label for **{info_b['name']}**:\n"
                f"> {info_b['interactions']}"
            )
            
    if warnings:
        return (
            f"### Possible FDA-Derived Drug Interaction Found\n\n"
            + "\n\n---\n\n".join(warnings)
            + "\n\n*Disclaimer: This warning is derived from parsed official product labels. Always consult a licensed medical provider before combining medications.*"
        )
        
    return (
        f"No dangerous drug interaction found in our local database or parsed FDA labels between '{medicine_a}' and '{medicine_b}'. "
        "However, this does not mean no interaction exists. Always verify with a healthcare provider before combining medications."
    )

# --- 4. symptom_checker ---
@tool
def symptom_checker(symptoms: str) -> str:
    """Evaluates symptoms against the local knowledge base and returns general home-care suggestions."""
    logger.info(f"Tool Call - Symptom Checker: {symptoms}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("symptom_checker")
    retriever = _get_retriever()
    docs = retriever.retrieve(symptoms, category_filter="Symptoms")
    if not docs:
        docs = retriever.retrieve(symptoms)
        
    if not docs:
        return "No matching symptom guides found in database. Recommend standard hydration, rest, and monitoring."
        
    return "\n\n".join([f"**From {doc.metadata.get('source_name', 'Symptoms Guide')}**:\n{doc.page_content}" for doc in docs])

# --- 5. disease_lookup ---
@tool
def disease_lookup(disease_name: str) -> str:
    """Searches the database for chronic diseases and clinical diagnosis / treatment guidelines."""
    logger.info(f"Tool Call - Disease Lookup: {disease_name}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("disease_lookup")
    retriever = _get_retriever()
    docs = retriever.retrieve(disease_name, category_filter="Diseases")
    if not docs:
        docs = retriever.retrieve(disease_name)
        
    if not docs:
        return "No diagnostic records match this disease in local vector databases."
        
    return "\n\n".join([f"**From {doc.metadata.get('source_name', 'Clinical Guidelines')}**:\n{doc.page_content}" for doc in docs])

# --- 6. nutrition_lookup ---
@tool
def nutrition_lookup(nutrient_or_food: str) -> str:
    """Provides evidence-based dietary recommendations, nutritional values, and food safety advice."""
    logger.info(f"Tool Call - Nutrition Lookup: {nutrient_or_food}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("nutrition_lookup")
    retriever = _get_retriever()
    docs = retriever.retrieve(nutrient_or_food, category_filter="Nutrition")
    if not docs:
        docs = retriever.retrieve(nutrient_or_food)
        
    if not docs:
        return f"No specific dietary records found for '{nutrient_or_food}'. Standard recommendation: Ensure a balanced diet of vegetables, fruits, whole grains, and lean proteins."
        
    return "\n\n".join([f"**From {doc.metadata.get('source_name', 'Nutrition Guide')}**:\n{doc.page_content}" for doc in docs])

# --- 7. pregnancy_lookup ---
@tool
def pregnancy_lookup(query: str) -> str:
    """Provides maternal, prenatal, and breastfeeding health guidelines."""
    logger.info(f"Tool Call - Pregnancy Lookup: {query}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("pregnancy_lookup")
    retriever = _get_retriever()
    docs = retriever.retrieve(query)
    
    preg_docs = [d for d in docs if "pregnancy" in d.metadata.get("category", "").lower() or "maternal" in d.metadata.get("source_name", "").lower() or "breastfeeding" in d.metadata.get("source_name", "").lower()]
    target_docs = preg_docs if preg_docs else docs
    
    if not target_docs:
        return "Refer to standard WHO guidelines: At least 8 ANC contacts, daily iron (30-60mg) + folic acid (400mcg) supplementation."
        
    return "\n\n".join([d.page_content for d in target_docs])

# --- Core First Aid Implementation ---
def _first_aid_impl(topic: str) -> str:
    """Core logic for step-by-step first aid guide."""
    logger.info(f"Tool Call - First Aid Guide: {topic}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("first_aid")
        
    guides = {
        "burn": (
            "1. **Cool the burn**: Run cool (not cold) tap water over it for 10 to 20 minutes.\n"
            "2. **Protect**: Remove rings or other tight items before the area swells. Cover with a clean bandage.\n"
            "3. **Do NOT**: Avoid popping blisters or applying butter, oils, or toothpaste.\n"
            "4. **Emergency Check**: Seek immediate medical care for deep burns, large burns, or burns on hands, face, or joints."
        ),
        "cut": (
            "1. **Stop Bleeding**: Apply gentle pressure with a clean cloth or bandage.\n"
            "2. **Clean**: Rinse the wound under clean running water. Wash around the wound with soap.\n"
            "3. **Apply Ointment**: Spread a thin layer of antibiotic ointment or petroleum jelly.\n"
            "4. **Cover**: Protect the cut with a sterile bandage.\n"
            "5. **Tetanus Warning**: Consult a physician if the cut was caused by rusty metal or soil, or if it is deep."
        ),
        "snake bite": (
            "1. **Safety First**: Move away from the snake. Do not try to capture it.\n"
            "2. **Stay Calm**: Keep the victim calm and still to slow the spread of venom.\n"
            "3. **Position**: Keep the bitten limb at or below heart level if possible.\n"
            "4. **Remove items**: Take off tight clothing or jewelry near the bite before swelling starts.\n"
            "5. **Do NOT**: Do not apply tourniquets, ice, or cut/try to suck out the venom.\n"
            "6. **Seek ER**: Get to the nearest emergency room immediately for antivenom."
        ),
        "electric shock": (
            "1. **Disconnect Power**: Do not touch the person if they are still in contact with the source. Turn off the main breaker.\n"
            "2. **Check responsiveness**: Once safe, check if the person is breathing. Call 911 immediately.\n"
            "3. **Start CPR**: If the person is not breathing or has no pulse, begin CPR.\n"
            "4. **Treat Burns**: If breathing, cover any visible burns with a sterile bandage."
        ),
        "choking": (
            "1. **Confirm**: Ask the person if they are choking. If they can speak, cough, or breathe, do not intervene.\n"
            "2. **Abdominal Thrusts (Heimlich)**: Stand behind the person, wrap your arms around their waist.\n"
            "3. **Position Fist**: Make a fist and place it slightly above the navel. Grasp with the other hand.\n"
            "4. **Thrust**: Pull upward and inward quickly and forcefully.\n"
            "5. **Unconscious**: If the person goes unconscious, lower them to the floor and begin CPR immediately."
        ),
        "fracture": (
            "1. **Stop bleeding**: Apply pressure to the wound with a clean bandage if skin is broken.\n"
            "2. **Immobilize**: Do not try to realign the bone. Apply a splint to support the area.\n"
            "3. **Apply Ice**: Place ice packs wrapped in a towel to reduce swelling.\n"
            "4. **Call Help**: Call emergency services if the bone has pierced the skin, or if pain is extreme."
        ),
        "heart attack": (
            "1. **Call 911**: Call emergency services immediately. Do not delay.\n"
            "2. **Chew Aspirin**: Have the person chew and swallow a regular aspirin (325mg) if they are not allergic.\n"
            "3. **Stay Calm**: Keep the person seated and quiet.\n"
            "4. **Monitor**: Prepare to begin CPR if the person becomes unresponsive or stops breathing."
        ),
        "stroke": (
            "1. **Act F.A.S.T.**:\n"
            "   - **F (Face)**: Ask the person to smile. Does one side of the face droop?\n"
            "   - **A (Arms)**: Ask them to raise both arms. Does one arm drift downward?\n"
            "   - **S (Speech)**: Ask them to repeat a simple phrase. Is their speech slurred?\n"
            "   - **T (Time)**: Call 911 immediately if any of these symptoms are present.\n"
            "2. **Do NOT**: Do not give the person food, drinks, or aspirin."
        ),
        "cpr": (
            "1. **Verify**: Check for breathing and responsiveness.\n"
            "2. **Call 911**: Call emergency services and get an AED if possible.\n"
            "3. **Compressions**: Place hands in center of chest and compress hard and fast (100-120 beats/min).\n"
            "4. **Rescue Breaths**: If trained, deliver 2 rescue breaths after every 30 compressions.\n"
            "5. **AED**: Turn on the AED as soon as it arrives and follow audio instructions."
        ),
        "poisoning": (
            "1. **Identify**: Note the container or substance if known.\n"
            "2. **Contact Poison Control**: Call your local poison control hotline immediately.\n"
            "3. **Inhaled**: Move the person to fresh air immediately.\n"
            "4. **Skin/Eyes**: Rinse thoroughly with water for at least 15 minutes.\n"
            "5. **Do NOT**: Do not induce vomiting unless specifically instructed by Poison Control."
        ),
        "nosebleed": (
            "1. **Sit Up**: Have the person sit up and lean forward slightly.\n"
            "2. **Pinch**: Pinch the soft part of the nose firmly for 10-15 minutes.\n"
            "3. **Breathe**: Encourage the person to breathe through their mouth.\n"
            "4. **Avoid**: Do not tilt the head back or blow the nose."
        ),
        "dog bite": (
            "1. **Clean**: Wash the wound thoroughly with soap and water for at least 5 minutes.\n"
            "2. **Apply Pressure**: Apply direct pressure with a clean cloth to control bleeding.\n"
            "3. **Cover**: Cover the wound with a sterile bandage.\n"
            "4. **Seek Medical Attention**: Visit a healthcare provider or emergency room within 24 hours."
        ),
        "bee sting": (
            "1. **Remove Stinger**: Carefully remove the stinger using a credit card or fingernail to scrape it out.\n"
            "2. **Clean**: Wash the area with soap and water.\n"
            "3. **Apply Cold Compress**: Apply a cold compress to reduce swelling and pain.\n"
            "4. **Monitor**: Watch for signs of an allergic reaction."
        ),
        "heat stroke": (
            "1. **Move to Cool Environment**: Move the person to a cooler place.\n"
            "2. **Remove Excess Clothing**: Remove any tight or unnecessary clothing.\n"
            "3. **Cool the Body**: Apply cool, wet cloths to the skin or immerse in cool water.\n"
            "4. **Hydrate**: If the person is conscious and able to swallow, give them cool water."
        ),
        "hypothermia": (
            "1. **Move to Warm Environment**: Move the person to a warmer place.\n"
            "2. **Remove Wet Clothing**: Take off any wet clothing and replace it with dry clothes.\n"
            "3. **Insulate**: Use blankets or sleeping bags to insulate the person.\n"
            "4. **Warm Drinks**: If the person is conscious and able to swallow, give them warm, non-alcoholic drinks."
        ),
        "drowning": (
            "1. **Call for Help**: Immediately call your local emergency services (911, 112, or 102).\n"
            "2. **Rescue**: If safe to do so, rescue the person from the water.\n"
            "3. **Check Breathing**: Check if the person is breathing and has a pulse.\n"
            "4. **Perform CPR**: If necessary, start cardiopulmonary resuscitation (CPR)."
        )
    }
    
    topic_key = topic.strip().lower()
    for k in guides:
        if k in topic_key:
            return f"### First Aid Instructions for {k.upper()}\n" + guides[k]
            
    return (
        f"Sorry, I don't have first aid instructions for '{topic}' in my local files. "
        "For any medical emergencies, please dial your local emergency services (911/112) immediately."
    )

# --- 8. first_aid & emergency_first_aid_guide ---
@tool
def first_aid(topic: str) -> str:
    """Retrieves step-by-step CPR/burn/snakebite first-aid guides from the local emergency definitions."""
    return _first_aid_impl(topic)

@tool
def emergency_first_aid_guide(topic: str) -> str:
    """Retrieves step-by-step first aid guide for a specific topic (e.g. burn, cut, snake bite, CPR)."""
    return _first_aid_impl(topic)

# --- 9. emergency_triage ---
@tool
def emergency_triage(complaint: str) -> str:
    """Evaluates safety critical symptoms and performs triage risk scoring."""
    logger.info(f"Tool Call - Emergency Triage: {complaint}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("emergency_triage")
        
    complaint_lower = complaint.lower()
    
    emergency_keywords = [
        "chest pain", "heart attack", "difficulty breathing", "shortness of breath",
        "loss of consciousness", "unresponsive", "stroke", "slurred speech",
        "paralysis", "allergic reaction", "anaphylaxis", "poisoning", "seizure", "suicidal"
    ]
    
    for sign in emergency_keywords:
        if sign in complaint_lower:
            return (
                f"### HIGH RISK CRITICAL EMERGENCY ESCALATION TRIGGERED\n"
                f"**Indicator**: '{sign.upper()}'\n"
                f"**Triage Class**: Tier 1 Critical Emergency\n"
                f"**Instructions**: Immediately halt and call your local emergency services (911, 112, or 102). "
                f"Do not attempt to drive yourself to the hospital."
            )
            
    for sign in EMERGENCY_SIGNS:
        if sign.lower() in complaint_lower:
            return (
                f"### HIGH RISK CRITICAL EMERGENCY ESCALATION TRIGGERED\n"
                f"**Indicator**: '{sign.upper()}'\n"
                f"**Triage Class**: Tier 1 Critical Emergency\n"
                f"**Instructions**: Immediately halt and call your local emergency services (911, 112, or 102). "
                f"Do not attempt to drive yourself to the hospital."
            )
            
    return (
        f"Triage Evaluation for '{complaint}': No acute Tier 1 red flags detected. "
        "Monitor symptoms closely and consult a primary care doctor if symptoms persist."
    )

# --- 10. bmi_calculator ---
@tool
def bmi_calculator(weight_kg: float, height_cm: float) -> str:
    """Calculates Body Mass Index (BMI) given weight in kg and height in cm."""
    logger.info(f"Tool Call - BMI Calculator: weight={weight_kg}, height={height_cm}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("bmi_calculator")
    if weight_kg <= 0 or height_cm <= 0:
        return "Error: Weight and height must be positive values."
        
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
        suggestion = "Consider speaking with a doctor or nutritionist about healthy ways to gain weight."
    elif 18.5 <= bmi < 24.9:
        category = "Normal weight"
        suggestion = "Great! Maintain your current balanced diet and regular physical activity."
    elif 25.0 <= bmi < 29.9:
        category = "Overweight"
        suggestion = "Consider incorporating more regular aerobic exercise and modifying caloric intake."
    else:
        category = "Obesity"
        suggestion = "We recommend consulting a doctor or dietitian to construct a safe and sustainable weight management plan."
        
    return (
        f"**Calculated BMI**: {bmi:.1f}\n"
        f"**Category**: {category}\n"
        f"**Healthy range**: 18.5 - 24.9\n"
        f"**Lifestyle suggestion**: {suggestion}"
    )

# --- 11. bmr_calculator ---
@tool
def bmr_calculator(age: int, gender: str, height_cm: float, weight_kg: float) -> str:
    """Calculates Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation. Gender must be 'male' or 'female'."""
    logger.info(f"Tool Call - BMR Calculator: age={age}, gender={gender}, height={height_cm}, weight={weight_kg}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("bmr_calculator")
    if age <= 0 or height_cm <= 0 or weight_kg <= 0:
        return "Error: Age, height, and weight must be positive numbers."
        
    gender_clean = gender.strip().lower()
    if gender_clean not in ["male", "female"]:
        return "Error: Gender must be 'male' or 'female'."
        
    if gender_clean == "male":
        bmr = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age + 5
    else:
        bmr = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age - 161
        
    return (
        f"**Estimated Basal Metabolic Rate (BMR)**: {bmr:.1f} kcal/day\n"
        f"This is the estimated amount of energy your body requires to function at rest."
    )

# --- 12. calorie_calculator ---
@tool
def calorie_calculator(age: int, gender: str, height_cm: float, weight_kg: float, activity_level: str) -> str:
    """Estimates daily caloric requirements (TDEE) based on BMR and physical activity level."""
    logger.info(f"Tool Call - Calorie Calculator: activity={activity_level}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("calorie_calculator")
    if age <= 0 or height_cm <= 0 or weight_kg <= 0:
        return "Error: Age, height, and weight must be positive numbers."
        
    gender_clean = gender.strip().lower()
    if gender_clean not in ["male", "female"]:
        return "Error: Gender must be 'male' or 'female'."
        
    if gender_clean == "male":
        bmr = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age + 5
    else:
        bmr = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age - 161
        
    activity_clean = activity_level.strip().lower()
    multipliers = {
        "sedentary": 1.2,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725
    }
    
    multiplier = multipliers.get(activity_clean)
    if not multiplier:
        return f"Error: Activity level must be one of {list(multipliers.keys())}"
        
    tdee = bmr * multiplier
    return (
        f"**Estimated Daily Caloric Needs (TDEE)**: {tdee:.0f} calories/day\n"
        f"**Calculated BMR**: {bmr:.1f} kcal/day\n"
        f"**Activity Level Multiplier**: {multiplier} ({activity_level})"
    )

# --- 13. water_calculator ---
@tool
def water_calculator(weight_kg: float) -> str:
    """Calculates recommended daily water intake (in Liters) based on weight."""
    logger.info(f"Tool Call - Water Calculator: weight={weight_kg}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("water_calculator")
    if weight_kg <= 0:
        return "Error: Weight must be a positive value."
        
    water_liters = weight_kg * 0.033
    return (
        f"**Recommended Daily Water Intake**: {water_liters:.2f} Liters\n"
        "Increase water intake during intense exercise, fever, or hot weather."
    )

# --- 14. medicine_dosage ---
@tool
def medicine_dosage(medicine_name: str) -> str:
    """Retrieves generic FDA-derived dosage guidelines for a specific medicine name."""
    logger.info(f"Tool Call - Medicine Dosage: {medicine_name}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("medicine_dosage")
        
    fda_info = get_fda_drug_info(medicine_name)
    if fda_info:
        return (
            f"### Official FDA Label Information\n\n"
            f"Standardized dosage must be verified from the official packaging or doctor's prescription.\n\n"
            f"Please consult your physician or the official product label."
        )
        
    return (
        f"General dosage guidelines for '{medicine_name}' not available. "
        "Standard guidance: Always follow package instructions and never double dose to catch up."
    )

# --- Core Unit Converter Implementation ---
def _unit_converter_impl(value: float, unit_from: str, unit_to: str) -> str:
    """Core conversion calculation."""
    logger.info(f"Tool Call - Unit Converter: value={value}, from={unit_from}, to={unit_to}")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("unit_converter")
    u_from = unit_from.strip().lower()
    u_to = unit_to.strip().lower()
    
    # Temperature
    if u_from in ["c", "celsius"] and u_to in ["f", "fahrenheit"]:
        res = (value * 9/5) + 32
        return f"{value}°C = {res:.2f}°F"
    elif u_from in ["f", "fahrenheit"] and u_to in ["c", "celsius"]:
        res = (value - 32) * 5/9
        return f"{value}°F = {res:.2f}°C"
        
    # Weight
    elif u_from in ["kg", "kilograms"] and u_to in ["lbs", "pounds", "lb"]:
        res = value * 2.20462
        return f"{value} kg = {res:.2f} lbs"
    elif u_from in ["lbs", "pounds", "lb"] and u_to in ["kg", "kilograms"]:
        res = value / 2.20462
        return f"{value} lbs = {res:.2f} kg"
        
    # Height
    elif u_from in ["cm", "centimeters"] and u_to in ["inches", "in", "inch"]:
        res = value * 0.393701
        return f"{value} cm = {res:.2f} inches"
    elif u_from in ["inches", "in", "inch"] and u_to in ["cm", "centimeters"]:
        res = value / 0.393701
        return f"{value} inches = {res:.2f} cm"
        
    # Blood Sugar
    elif u_from == "mg/dl" and u_to == "mmol/l":
        res = value / 18.018
        return f"{value} mg/dL = {res:.3f} mmol/L"
    elif u_from == "mmol/l" and u_to == "mg/dl":
        res = value * 18.018
        return f"{value} mmol/L = {res:.1f} mg/dL"
        
    return f"Conversion from '{unit_from}' to '{unit_to}' is not supported."

# --- 15. medical_unit_converter & unit_converter ---
@tool
def medical_unit_converter(value: float, unit_from: str, unit_to: str) -> str:
    """Converts health-related units (Temperature, Weight, Height, Blood sugar)."""
    return _unit_converter_impl(value, unit_from, unit_to)

@tool
def unit_converter(value: float, unit_from: str, unit_to: str) -> str:
    """Converts health-related units (Temperature: C <-> F, Weight: kg <-> lbs, Height: cm <-> inches, Blood Sugar: mg/dL <-> mmol/L)."""
    return _unit_converter_impl(value, unit_from, unit_to)

# --- 16. health_tips ---
@tool
def health_tips(query: str = "") -> str:
    """Generates custom health advice tips based on the active patient profile."""
    logger.info("Tool Call - Health Tips")
    if "executed_tools" in st.session_state:
        st.session_state["executed_tools"].append("health_tips")
        
    profile = st.session_state.get("patient_profile", {})
    tips = []
    
    if profile.get("allergies"):
        tips.append(f"- Keep a detailed medical alert card listing your allergies ({profile['allergies']}) with you.")
    if profile.get("known_diseases") and "diabetes" in profile["known_diseases"].lower():
        tips.append("- Maintain regular blood glucose monitoring and dietary fiber intake.")
    if profile.get("known_diseases") and "hypertension" in profile["known_diseases"].lower():
        tips.append("- Restrict dietary sodium intake below 2,000 mg daily and monitor blood pressure.")
    if profile.get("current_medicines"):
        tips.append("- Always take medications on schedule as prescribed by your doctor.")
    if profile.get("age"):
        try:
            if int(profile["age"]) >= 60:
                tips.append("- Schedule regular preventive health check-ups and vision screenings.")
        except Exception:
            pass
        
    tips.append("- Physical activity: Aim for 150-300 minutes of moderate aerobic exercise weekly.")
    tips.append("- Diet: Consume a variety of fresh vegetables, fruits, and lean proteins daily.")
    tips.append("- Hydration: Drink adequate water throughout the day to support metabolic health.")
    
    return "### Clinical Health Tips:\n" + "\n".join(tips)

# Gather all 16 tools into a single list
all_tools = [
    medical_rag,
    medicine_lookup,
    drug_interactions,
    symptom_checker,
    disease_lookup,
    nutrition_lookup,
    pregnancy_lookup,
    first_aid,
    emergency_triage,
    bmi_calculator,
    bmr_calculator,
    calorie_calculator,
    water_calculator,
    medicine_dosage,
    medical_unit_converter,
    health_tips
]

# Backward compatibility aliases
water_intake_calculator = water_calculator
calorie_estimator = calorie_calculator
medicine_information = medicine_lookup
drug_interaction_checker = drug_interactions
