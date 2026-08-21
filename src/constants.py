# Core Application Constants

# List of knowledge base subcategories to index and display status for
KNOWLEDGE_CATEGORIES = [
    "Symptoms",
    "Diseases",
    "Medicines",
    "Drug_Interactions",
    "Drug_Side_Effects",
    "Nutrition",
    "Pregnancy",
    "Diabetes",
    "Hypertension",
    "Mental_Health",
    "Emergency",
    "First_Aid",
    "Vaccination",
    "Lifestyle",
    "Healthcare_FAQ"
]

# Greetings mapping for direct agent replies
GREETING_WORDS = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon", "greetings", "yo"}

# Medical Warning Signs to append or highlight in responses
EMERGENCY_SIGNS = [
    "Sudden, severe chest pain or pressure",
    "Difficulty breathing or severe shortness of breath",
    "Sudden numbness or weakness, especially on one side of the body",
    "Difficulty speaking or understanding speech",
    "Sudden changes in vision",
    "Severe, sudden headache with no known cause",
    "Loss of consciousness or severe confusion"
]

# Default JSON datasets for tool lookup to ensure robustness without external network dependency
DEFAULT_MEDICINES = {
    "paracetamol": {
        "name": "Paracetamol (Acetaminophen)",
        "generic": "Acetaminophen",
        "uses": "Temporary relief of mild to moderate pain (headaches, muscle aches, toothaches) and reducing fever.",
        "side_effects": "Rare when taken at recommended doses. High doses can cause serious liver damage. Allergic reactions (rash, swelling) are very rare.",
        "warnings": "Do not exceed 4000 mg in 24 hours. Avoid alcohol. Check other cold/flu meds to prevent double-dosing.",
        "storage": "Store at room temperature away from direct heat and moisture.",
        "interactions": "Alcohol increases risk of liver toxicity. Warfarin (long-term use) may have increased bleeding risks."
    },
    "aspirin": {
        "name": "Aspirin (Acetylsalicylic Acid)",
        "generic": "Acetylsalicylic Acid",
        "uses": "Pain relief, reducing inflammation, reducing fever, and preventing blood clots (low dose cardiovascular therapy).",
        "side_effects": "Stomach upset, heartburn, easy bruising or bleeding, increased risk of stomach ulcers.",
        "warnings": "Do not give to children or teenagers due to Reye's syndrome risk. Do not use if you have bleeding disorders or active stomach ulcers.",
        "storage": "Store in a dry place at room temperature. Keep tightly closed.",
        "interactions": "Interacts with blood thinners (Warfarin), NSAIDs (Ibuprofen), and corticosteroids."
    },
    "ibuprofen": {
        "name": "Ibuprofen",
        "generic": "Ibuprofen",
        "uses": "Relief of pain, inflammation, and stiffness caused by arthritis, menstrual cramps, headache, toothache, and back pain.",
        "side_effects": "Nausea, vomiting, diarrhea, bloating, constipation, dizziness, high blood pressure.",
        "warnings": "Take with food or milk to prevent stomach upset. Can increase risk of heart attack or stroke if used long-term or at high doses.",
        "storage": "Store in a dry place at room temperature. Protect from light.",
        "interactions": "Interacts with aspirin, blood pressure medications (ACE inhibitors like Lisinopril), and blood thinners."
    },
    "metformin": {
        "name": "Metformin",
        "generic": "Metformin Hydrochloride",
        "uses": "Management of Type 2 diabetes to improve blood sugar control.",
        "side_effects": "Nausea, upset stomach, diarrhea, metallic taste in mouth. Rare but serious risk of lactic acidosis.",
        "warnings": "Do not use in patients with severe kidney disease. Avoid heavy alcohol intake while taking Metformin.",
        "storage": "Store at room temperature away from light and moisture.",
        "interactions": "Cimetidine, contrast dyes used for imaging (may require temporary suspension)."
    },
    "amoxicillin": {
        "name": "Amoxicillin",
        "generic": "Amoxicillin",
        "uses": "Treatment of bacterial infections such as ear infections, strep throat, pneumonia, and urinary tract infections.",
        "side_effects": "Diarrhea, nausea, vomiting, skin rash, yeast infection.",
        "warnings": "Finish the entire prescribed course even if symptoms disappear. Do not use if you are allergic to penicillin.",
        "storage": "Capsules: store at room temperature. Liquid: store in refrigerator (do not freeze) and discard after 14 days.",
        "interactions": "May reduce the effectiveness of oral contraceptives. Allopurinol may increase risk of rash."
    }
}

DEFAULT_INTERACTIONS = {
    "aspirin+warfarin": {
        "drugs": ["Aspirin", "Warfarin"],
        "severity": "Major",
        "mechanism": "Both medications thin the blood. Combining them significantly increases the risk of serious bleeding (gastrointestinal or internal).",
        "recommendation": "Avoid simultaneous use unless specifically prescribed and monitored by a doctor. Regular blood clotting tests (INR) will be required."
    },
    "ibuprofen+lisinopril": {
        "drugs": ["Ibuprofen", "Lisinopril"],
        "severity": "Moderate",
        "mechanism": "NSAIDs like Ibuprofen can reduce the blood-pressure-lowering effects of ACE inhibitors like Lisinopril. It may also increase the risk of kidney impairment, especially in elderly or dehydrated patients.",
        "recommendation": "Monitor blood pressure regularly. Ensure adequate hydration. Consult a physician for alternative pain management if used long-term."
    },
    "metformin+alcohol": {
        "drugs": ["Metformin", "Alcohol"],
        "severity": "Major",
        "mechanism": "Alcohol can increase the risk of Metformin-induced lactic acidosis, a rare but life-threatening condition characterized by deep/rapid breathing, muscle pain, and extreme fatigue.",
        "recommendation": "Avoid excessive or chronic alcohol consumption while taking Metformin."
    },
    "aspirin+ibuprofen": {
        "drugs": ["Aspirin", "Ibuprofen"],
        "severity": "Moderate",
        "mechanism": "Ibuprofen can interfere with the antiplatelet effect of low-dose aspirin used for cardioprotection, making aspirin less effective. It also increases gastrointestinal bleeding risks.",
        "recommendation": "If taking both, take aspirin at least 30 minutes before or 8 hours after taking ibuprofen, or consult a doctor for options."
    }
}
