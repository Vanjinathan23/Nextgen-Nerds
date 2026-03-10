"""
AI Clinical Copilot Service
Gemini-powered diagnosis suggestion engine with rule-based fallback.
"""
import json
import random
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# Knowledge base: symptom -> condition mappings with confidence (Fallback)
CONDITION_DB = {
    "Chest pain": [
        {"condition": "Acute Coronary Syndrome", "confidence": 0.75, "tests": ["Troponin", "ECG", "Chest X-ray"], "specialist": "Cardiologist"},
        {"condition": "Costochondritis", "confidence": 0.40, "tests": ["Physical Exam"], "specialist": ""},
        {"condition": "Pulmonary Embolism", "confidence": 0.55, "tests": ["D-Dimer", "CT Pulmonary Angiography"], "specialist": "Pulmonologist"},
        {"condition": "GERD", "confidence": 0.35, "tests": ["Endoscopy", "pH Monitoring"], "specialist": "Gastroenterologist"},
    ],
    "Shortness of breath": [
        {"condition": "Pneumonia", "confidence": 0.65, "tests": ["Chest X-ray", "CBC", "Sputum Culture"], "specialist": "Pulmonologist"},
        {"condition": "Heart Failure", "confidence": 0.60, "tests": ["BNP", "Echocardiogram", "Chest X-ray"], "specialist": "Cardiologist"},
        {"condition": "Asthma Exacerbation", "confidence": 0.55, "tests": ["Spirometry", "Peak Flow"], "specialist": "Pulmonologist"},
        {"condition": "COPD Exacerbation", "confidence": 0.50, "tests": ["ABG", "Chest X-ray", "Spirometry"], "specialist": "Pulmonologist"},
    ],
    "Headache": [
        {"condition": "Migraine", "confidence": 0.70, "tests": ["Neurological Exam"], "specialist": "Neurologist"},
        {"condition": "Tension Headache", "confidence": 0.65, "tests": ["Physical Exam"], "specialist": ""},
        {"condition": "Intracranial Hemorrhage", "confidence": 0.30, "tests": ["CT Head", "MRI Brain"], "specialist": "Neurologist"},
        {"condition": "Meningitis", "confidence": 0.25, "tests": ["Lumbar Puncture", "Blood Culture", "CT Head"], "specialist": "Infectious Disease"},
    ],
    "Dizziness": [
        {"condition": "Benign Positional Vertigo", "confidence": 0.60, "tests": ["Dix-Hallpike Test"], "specialist": "ENT"},
        {"condition": "Orthostatic Hypotension", "confidence": 0.50, "tests": ["Orthostatic Vitals", "CBC"], "specialist": ""},
        {"condition": "Vestibular Neuritis", "confidence": 0.40, "tests": ["MRI Brain", "Audiometry"], "specialist": "ENT"},
        {"condition": "Stroke", "confidence": 0.35, "tests": ["CT Head", "MRI Brain", "CT Angiography"], "specialist": "Neurologist"},
    ],
    "Nausea": [
        {"condition": "Gastroenteritis", "confidence": 0.65, "tests": ["Stool Culture", "CBC"], "specialist": "Gastroenterologist"},
        {"condition": "Gastroparesis", "confidence": 0.40, "tests": ["Gastric Emptying Study"], "specialist": "Gastroenterologist"},
        {"condition": "Appendicitis", "confidence": 0.35, "tests": ["CT Abdomen", "CBC", "Urinalysis"], "specialist": "Surgeon"},
    ],
    "Fatigue": [
        {"condition": "Anemia", "confidence": 0.60, "tests": ["CBC", "Iron Studies", "Reticulocyte Count"], "specialist": "Hematologist"},
        {"condition": "Hypothyroidism", "confidence": 0.55, "tests": ["TSH", "Free T4"], "specialist": "Endocrinologist"},
        {"condition": "Depression", "confidence": 0.45, "tests": ["PHQ-9 Screening"], "specialist": "Psychiatrist"},
        {"condition": "Diabetes", "confidence": 0.40, "tests": ["Fasting Glucose", "HbA1c"], "specialist": "Endocrinologist"},
    ],
    "Fever": [
        {"condition": "Upper Respiratory Infection", "confidence": 0.70, "tests": ["Rapid Strep", "Monospot"], "specialist": ""},
        {"condition": "Urinary Tract Infection", "confidence": 0.55, "tests": ["Urinalysis", "Urine Culture"], "specialist": ""},
        {"condition": "Pneumonia", "confidence": 0.50, "tests": ["Chest X-ray", "CBC", "Blood Culture"], "specialist": "Pulmonologist"},
        {"condition": "Sepsis", "confidence": 0.30, "tests": ["Blood Culture", "Lactate", "CBC", "CRP"], "specialist": "Intensivist"},
    ],
    "Cough": [
        {"condition": "Bronchitis", "confidence": 0.65, "tests": ["Chest X-ray"], "specialist": ""},
        {"condition": "Pneumonia", "confidence": 0.55, "tests": ["Chest X-ray", "CBC", "Sputum Culture"], "specialist": "Pulmonologist"},
        {"condition": "Tuberculosis", "confidence": 0.30, "tests": ["TB Skin Test", "Chest X-ray", "Sputum AFB"], "specialist": "Infectious Disease"},
        {"condition": "Lung Cancer", "confidence": 0.15, "tests": ["CT Chest", "Bronchoscopy"], "specialist": "Oncologist"},
    ],
    "Abdominal pain": [
        {"condition": "Appendicitis", "confidence": 0.55, "tests": ["CT Abdomen", "CBC", "Urinalysis"], "specialist": "Surgeon"},
        {"condition": "Cholecystitis", "confidence": 0.50, "tests": ["RUQ Ultrasound", "LFTs", "CBC"], "specialist": "Surgeon"},
        {"condition": "Peptic Ulcer Disease", "confidence": 0.45, "tests": ["H. pylori Test", "Endoscopy"], "specialist": "Gastroenterologist"},
        {"condition": "Pancreatitis", "confidence": 0.40, "tests": ["Lipase", "Amylase", "CT Abdomen"], "specialist": "Gastroenterologist"},
    ],
}


def analyze_patient(symptoms: list, vitals: dict = None, history: list = None, lab_results: list = None) -> dict:
    """Analyze patient data and suggest possible diagnoses using Gemini if available."""
    
    if model:
        try:
            prompt = f"""
            You are a Clinical Decision Support AI. Analyze the following patient data:
            Symptoms: {', '.join(symptoms)}
            Vitals: {json.dumps(vitals) if vitals else 'Not provided'}
            Medical History: {', '.join(history) if history else 'Not provided'}
            Lab Results: {json.dumps(lab_results) if lab_results else 'Not provided'}
            
            Provide a detailed clinical analysis in JSON format:
            {{
                "possible_conditions": [
                    {{ "name": "Condition Name", "confidence": 0-100, "supporting_symptoms": [] }}
                ],
                "recommended_tests": [],
                "specialist_referrals": [],
                "clinical_notes": []
            }}
            Only return the JSON.
            """
            response = model.generate_content(prompt)
            # Find and parse JSON from response
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            return result
        except Exception as e:
            print(f"Gemini analysis error: {e}. Falling back to rule-based engine.")

    # Rule-based fallback
    conditions = {}
    all_tests = set()
    all_specialists = set()

    for symptom in symptoms:
        if symptom in CONDITION_DB:
            for entry in CONDITION_DB[symptom]:
                cond = entry["condition"]
                if cond in conditions:
                    conditions[cond]["confidence"] = min(0.95, conditions[cond]["confidence"] + entry["confidence"] * 0.3)
                    conditions[cond]["supporting_symptoms"].append(symptom)
                else:
                    conditions[cond] = {
                        "confidence": entry["confidence"],
                        "supporting_symptoms": [symptom],
                    }
                all_tests.update(entry["tests"])
                if entry["specialist"]:
                    all_specialists.add(entry["specialist"])

    # Adjust confidence based on vitals
    if vitals:
        if vitals.get("oxygen_level", 100) < 92:
            for c in ["Pneumonia", "Heart Failure", "COPD Exacerbation", "Pulmonary Embolism"]:
                if c in conditions:
                    conditions[c]["confidence"] = min(0.95, conditions[c]["confidence"] + 0.15)
        if vitals.get("heart_rate", 72) > 110:
            for c in ["Atrial Fibrillation", "Supraventricular Tachycardia", "Sepsis"]:
                if c in conditions:
                    conditions[c]["confidence"] = min(0.95, conditions[c]["confidence"] + 0.10)

    # Sort conditions by confidence
    sorted_conditions = sorted(conditions.items(), key=lambda x: x[1]["confidence"], reverse=True)

    return {
        "possible_conditions": [
            {"name": name, "confidence": round(data["confidence"] * 100, 1), "supporting_symptoms": data["supporting_symptoms"]}
            for name, data in sorted_conditions[:6]
        ],
        "recommended_tests": sorted(list(all_tests))[:10],
        "specialist_referrals": sorted(list(all_specialists)),
        "clinical_notes": _generate_clinical_notes(symptoms, sorted_conditions),
    }


def _generate_clinical_notes(symptoms, conditions):
    notes = []
    if len(symptoms) > 3:
        notes.append("Multiple concurrent symptoms suggest complex presentation. Comprehensive workup recommended.")
    if conditions and conditions[0][1]["confidence"] > 0.7:
        notes.append(f"High-confidence preliminary diagnosis: {conditions[0][0]}. Confirmatory testing advised.")
    if not notes:
        notes.append("Standard evaluation recommended. Monitor for symptom progression.")
    return notes
