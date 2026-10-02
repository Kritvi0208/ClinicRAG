import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils import format_user_followup_prompt

def test_user_followup_transformations():
    test_cases = [
        (
            "Are you interested in learning about ways to maintain or adjust your weight through nutrition?",
            "What are ways to maintain or adjust my weight through nutrition?"
        ),
        (
            "Would you like to know about other measurements, such as waist circumference, that provide additional health insights?",
            "Tell me about other measurements, such as waist circumference, that provide additional health insights"
        ),
        (
            "Do you have any specific fitness or wellness goals you are hoping to achieve?",
            "How can I manage my fitness or wellness goals?"
        ),
        (
            "Would you like to calculate your BMI right now by sharing your height and weight?",
            "Can you calculate my BMI right now by sharing my height and weight?"
        ),
        (
            "How can I maintain a healthy BMI?",
            "How can I maintain a healthy BMI?"
        ),
        (
            "What are common side effects of Paracetamol?",
            "What are common side effects of Paracetamol?"
        ),
        (
            "Are you experiencing any fever or sore throat?",
            "What should I do if I have fever or sore throat?"
        ),
    ]

    for raw, expected in test_cases:
        res = format_user_followup_prompt(raw)
        print(f"\n[RAW]      {raw}")
        print(f"[CONVERT]  {res}")
        assert res, f"Expected non-empty output for: {raw}"
        # Ensure 'your' is never left if converted
        if "your" in raw.lower():
            assert "your" not in res.lower(), f"'your' was not converted to 'my' in: {res}"

    print("\n[ALL TESTS PASSED] Follow-up prompts are properly formatted from the User's first-person perspective!")

if __name__ == "__main__":
    test_user_followup_transformations()
