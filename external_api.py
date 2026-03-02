import random

def search_external_guidelines(disease: str, microorganism: str) -> list:
    """
    Mock external API lookup.
    Returns a list of drug recommendations for the given disease/microorganism.
    Each recommendation is a dict with keys: drug_name, aware_category, spectrum, class,
    standard_dose, duration, rationale, source, score_modifier.
    """
    disease_lower = disease.lower()
    mo_lower = microorganism.lower() if microorganism else ""

    # Mock database of external guidelines
    external_data = {
        "gonorrhea": [
            {
                "drug_name": "Ceftriaxone",
                "aware_category": "Watch",
                "spectrum": "Broad",
                "class": "Cephalosporin",
                "standard_dose": "250 mg IM",
                "duration": "single dose",
                "rationale": "First-line per CDC/WHO for uncomplicated gonorrhea",
                "source": "CDC 2024",
                "score_modifier": 25
            },
            {
                "drug_name": "Cefixime",
                "aware_category": "Watch",
                "spectrum": "Broad",
                "class": "Cephalosporin",
                "standard_dose": "400 mg oral",
                "duration": "single dose",
                "rationale": "Alternative when ceftriaxone not available",
                "source": "CDC 2024",
                "score_modifier": 15
            }
        ],
        "meningitis": [
            {
                "drug_name": "Ceftriaxone",
                "aware_category": "Watch",
                "spectrum": "Broad",
                "class": "Cephalosporin",
                "standard_dose": "2 g IV q12h",
                "duration": "7-14 days",
                "rationale": "Empiric therapy for bacterial meningitis",
                "source": "IDSA Guidelines",
                "score_modifier": 25
            },
            {
                "drug_name": "Vancomycin",
                "aware_category": "Reserve",
                "spectrum": "Narrow",
                "class": "Glycopeptide",
                "standard_dose": "15-20 mg/kg IV q8-12h",
                "duration": "7-14 days",
                "rationale": "Plus ceftriaxone for empiric coverage of resistant pneumococci",
                "source": "IDSA Guidelines",
                "score_modifier": 20
            }
        ],
        "tuberculosis": [
            {
                "drug_name": "Rifampicin",
                "aware_category": "Access",
                "spectrum": "Broad",
                "class": "Rifamycin",
                "standard_dose": "10 mg/kg daily",
                "duration": "6 months",
                "rationale": "First-line anti-TB therapy (with INH, pyrazinamide, ethambutol)",
                "source": "WHO",
                "score_modifier": 30
            }
        ]
    }

    # Check if disease matches any known external guidelines
    for key, recommendations in external_data.items():
        if key in disease_lower or (mo_lower and key in mo_lower):
            return recommendations

    # If no match, return empty list (system will fall back to empiric Access drugs)
    return []