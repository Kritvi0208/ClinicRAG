import sys
import os
import unittest
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import config
from src.utils import clean_text, time_formatter, token_counter
from src.loaders import MedicalDocumentLoader
from src.splitter import MedicalTextSplitter
from src.tools import (
    bmi_calculator,
    bmr_calculator,
    water_calculator,
    calorie_calculator,
    unit_converter,
    emergency_first_aid_guide,
    medicine_lookup,
    drug_interactions,
    symptom_checker,
    disease_lookup,
    nutrition_lookup,
    pregnancy_lookup,
    emergency_triage,
    medicine_dosage,
    health_tips,
    # Compatibility aliases
    water_intake_calculator,
    calorie_estimator,
    medicine_information,
    drug_interaction_checker
)
from src.prompts import get_agent_prompt_template
from src.router import IntentRouter
from src.memory import MedicalMemory

class TestClinicRAGComponents(unittest.TestCase):
    
    def test_utils(self):
        """Test utility helper functions."""
        self.assertEqual(clean_text("  Hello   World! \n"), "Hello World!")
        self.assertEqual(time_formatter(0.005), "5.00 ms")
        self.assertEqual(time_formatter(2.5), "2.50 seconds")
        self.assertGreater(token_counter("Testing the token counter functionality"), 0)

    def test_calculators(self):
        """Test health calculators and conversion tools."""
        # BMI
        bmi_res = bmi_calculator.invoke({"weight_kg": 70, "height_cm": 175})
        self.assertIn("Calculated BMI**: 22.9", bmi_res)
        self.assertIn("Normal weight", bmi_res)
        
        # BMR
        bmr_res = bmr_calculator.invoke({"age": 25, "gender": "male", "height_cm": 180, "weight_kg": 80})
        self.assertIn("Basal Metabolic Rate", bmr_res)
        self.assertIn("1805.0", bmr_res)
        
        # Water
        water_res = water_intake_calculator.invoke({"weight_kg": 70})
        self.assertIn("2.31 Liters", water_res)
        
        # TDEE Calorie Calculator
        calorie_res = calorie_estimator.invoke({
            "age": 25,
            "gender": "male",
            "height_cm": 180,
            "weight_kg": 80,
            "activity_level": "moderately active"
        })
        self.assertIn("Estimated Daily Caloric Needs (TDEE)**: 2798", calorie_res)

    def test_unit_converter(self):
        """Test unit conversion values."""
        self.assertIn("37.00°C", unit_converter.invoke({"value": 98.6, "unit_from": "F", "unit_to": "C"}))
        self.assertIn("154.32 lbs", unit_converter.invoke({"value": 70, "unit_from": "kg", "unit_to": "lbs"}))
        self.assertIn("5.550 mmol/L", unit_converter.invoke({"value": 100, "unit_from": "mg/dL", "unit_to": "mmol/L"}))
        self.assertIn("180.2 mg/dL", unit_converter.invoke({"value": 10, "unit_from": "mmol/L", "unit_to": "mg/dL"}))

    def test_static_databases(self):
        """Test local JSON database tools (medicines and interactions)."""
        # Medicine info
        med_res = medicine_information.invoke({"medicine_name": "paracetamol"})
        self.assertIn("Acetaminophen", med_res)
        
        # Non-existent medicine fallback
        missing_res = medicine_information.invoke({"medicine_name": "non_existent_drug"})
        self.assertIn("do not have pre-verified pharmaceutical information", missing_res)
        
        # Drug interaction
        interaction_res = drug_interaction_checker.invoke({"medicine_a": "aspirin", "medicine_b": "warfarin"})
        self.assertIn("Major", interaction_res)
        self.assertIn("bleed", interaction_res.lower())

    def test_first_aid_guide(self):
        """Test emergency first aid information recovery."""
        cpr_res = emergency_first_aid_guide.invoke({"topic": "CPR"})
        self.assertIn("Compressions", cpr_res)
        
        burn_res = emergency_first_aid_guide.invoke({"topic": "burn"})
        self.assertIn("Cool the burn", burn_res)

    def test_new_tools(self):
        """Test the newly registered clinical and profiling tools."""
        # Emergency Triage
        triage_res = emergency_triage.invoke({"complaint": "I have severe sudden chest pain"})
        self.assertIn("CRITICAL EMERGENCY", triage_res)
        
        # Health Tips
        tips_res = health_tips.invoke({"query": ""})
        self.assertIn("Physical activity", tips_res)
        
        # Medicine Dosage
        dosage_res = medicine_dosage.invoke({"medicine_name": "alcohol"})
        self.assertIn("dosage", dosage_res.lower())

    def test_loaders_and_splitters(self):
        """Test doc loader and recursive characters text splitter."""
        loader = MedicalDocumentLoader(config.KNOWLEDGE_BASE_DIR)
        docs = loader.load()
        self.assertGreater(len(docs), 0)
        
        splitter = MedicalTextSplitter(chunk_size=200, chunk_overlap=20)
        chunks = splitter.split_documents(docs)
        self.assertGreater(len(chunks), len(docs))
        self.assertEqual(chunks[0].metadata["chunk_id"], f"{chunks[0].metadata['source_name']}_chunk_0")

    def test_agent_prompt(self):
        """Verify prompt templates compile correctly."""
        prompt = get_agent_prompt_template()
        self.assertIn("agent_scratchpad", prompt.input_variables)
        self.assertIn("chat_history", prompt.input_variables)

    def test_intent_router_rules(self):
        """Verify that rule-based safety bypass works for red-flag inputs."""
        router = IntentRouter()
        # Test instant red-flag bypass
        res = router.classify("I think I am having a heart attack right now")
        self.assertTrue(res["emergency_bypass"])
        self.assertIn("Emergency", res["intents"])
        self.assertEqual(res["matched_flag"], "heart attack")

if __name__ == "__main__":
    unittest.main()
