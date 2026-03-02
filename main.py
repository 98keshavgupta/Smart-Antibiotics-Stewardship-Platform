from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import sqlite3
import universal_api
import external_api
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    disease: str
    microorganism: str
    location: str
    age: Optional[int] = 30
    sex: Optional[str] = "Male"
    pregnancy: Optional[bool] = False
    allergy: Optional[str] = ""
    crcl: Optional[float] = None
    lfts: Optional[str] = ""

class PatientSaveData(RequestData):
    recommended_drug: str
    dose: str
    sensitivity: str
    aware: str
    rationale: str

def get_db_connection():
    conn = sqlite3.connect('stewardship.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_drug_line_bonus(disease: str, drug_name: str) -> int:
    """Return bonus points based on drug line for this disease (now reduced to a small tie‑breaker)."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT line FROM disease_drug_lines WHERE LOWER(disease_keyword) LIKE LOWER(?) AND drug_name = ?",
              (f"%{disease}%", drug_name))
    row = c.fetchone()
    conn.close()
    if row:
        line = row['line']
        if line == 1:
            return 5   # reduced from 15
        elif line == 2:
            return 3   # reduced from 8
        elif line == 3:
            return 1   # reduced from 3
    return 0

def calculate_drug_score(drug: Dict[str, Any], sensitivity: Optional[float], disease: str,
                         is_guideline_match: bool = False, external_score_modifier: int = 0) -> int:
    """
    Score a drug with sensitivity as the dominant factor.
    Higher sensitivity gives much higher points.
    AWaRe category and spectrum provide moderate boosts.
    Drug line now provides only a small tie‑breaker.
    """
    score = 0
    if sensitivity is not None:
        if sensitivity >= 90:
            score += 30          # very high sensitivity
        elif sensitivity >= 80:
            score += 25
        elif sensitivity >= 70:
            score += 20
        elif sensitivity >= 60:
            score += 15
        elif sensitivity >= 50:
            score += 10
        elif sensitivity >= 30:
            score += 5            # marginal

    # AWaRe category: Access > Watch > Reserve
    if drug['aware_category'] == 'Access':
        score += 15
    elif drug['aware_category'] == 'Watch':
        score += 10
    elif drug['aware_category'] == 'Reserve':
        score += 5

    # Narrow spectrum preferred
    if drug['spectrum'] == 'Narrow':
        score += 8

    # Guideline match bonus (small)
    if is_guideline_match:
        score += 5

    # Drug line bonus (now small tie‑breaker)
    line_bonus = get_drug_line_bonus(disease, drug['name'])
    score += line_bonus

    # External source bonus (if any)
    score += external_score_modifier

    return score

def build_rationale(drug: Dict[str, Any], sensitivity: Optional[float], data: RequestData,
                    is_guideline_match: bool, has_local_data: bool, line_bonus: int,
                    is_broadened: bool = False, external_source: str = None) -> str:
    parts = []
    if sensitivity is not None:
        parts.append(f"Local susceptibility {sensitivity}%")
        if sensitivity < 50:
            parts.append("**reduced susceptibility** – consider cautiously")
    elif external_source:
        parts.append(f"External guideline ({external_source})")
    else:
        parts.append("No local data – using global guideline")

    parts.append(f"{drug['aware_category']} antibiotic")
    if drug['spectrum'] == 'Narrow':
        parts.append("narrow spectrum (preferred to minimise resistance)")
    else:
        parts.append("broad spectrum")

    if data.pregnancy and drug['pregnancy_safe']:
        parts.append("safe in pregnancy")
    elif data.pregnancy and not drug['pregnancy_safe']:
        parts.append("CAUTION: not safe in pregnancy")

    if data.allergy:
        parts.append(f"no cross-allergy with {data.allergy}")

    if data.crcl and drug['renal_adjustment_needed'] and data.crcl < 30:
        parts.append("renal adjustment required")

    if is_guideline_match:
        parts.append("matches global guideline")

    line_info = ""
    if line_bonus >= 5:
        line_info = "first-line"
    elif line_bonus >= 3:
        line_info = "second-line"
    elif line_bonus >= 1:
        line_info = "alternative"
    if line_info:
        parts.append(f"{line_info} for this disease")

    if is_broadened:
        parts.append("included to provide additional options")

    base = " – ".join(parts)
    return base.capitalize()

def get_dose_string(drug: Dict[str, Any], data: RequestData) -> str:
    dose = drug.get('standard_dose', 'Standard dose')
    duration = drug.get('duration', '')
    base = f"{dose} for {duration}" if duration else dose

    if data.crcl and drug.get('renal_adjustment_needed') and data.crcl < 30:
        renal_adj = drug.get('renal_dose_adjustment')
        if renal_adj:
            return f"{renal_adj} (CrCl < 30)"
        else:
            return f"Reduce dose (CrCl < 30) – {base}"
    return base

@app.post("/api/step1_search")
def step1_search(data: RequestData):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT drug_name, sensitivity_percent 
        FROM antibiograms 
        WHERE LOWER(TRIM(microorganism)) = LOWER(TRIM(?)) 
          AND LOWER(TRIM(location)) = LOWER(TRIM(?))
    """, (data.microorganism, data.location))
    local_data = c.fetchall()
    research_data = universal_api.get_live_research_data(data.disease, data.microorganism)
    conn.close()
    return {
        "local_sensitivity": [dict(row) for row in local_data],
        "external_research": research_data,
        "message": "Data fetched."
    }

@app.post("/api/step2_recommend")
def step2_recommend(data: RequestData):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM drugs")
    all_drugs = [dict(row) for row in c.fetchall()]

    # Local antibiogram data
    c.execute("""
        SELECT drug_name, sensitivity_percent 
        FROM antibiograms 
        WHERE LOWER(TRIM(microorganism)) = LOWER(TRIM(?)) 
          AND LOWER(TRIM(location)) = LOWER(TRIM(?))
    """, (data.microorganism, data.location))
    sensitivity_map = {row['drug_name']: row['sensitivity_percent'] for row in c.fetchall()}
    has_local_data = len(sensitivity_map) > 0

    # Global guidelines (from local database)
    c.execute("""
        SELECT recommended_drug 
        FROM global_guidelines 
        WHERE LOWER(disease_keyword) LIKE LOWER(?)
    """, (f"%{data.disease}%",))
    guideline_rows = c.fetchall()
    guideline_drugs = [row['recommended_drug'] for row in guideline_rows]

    strict_recommendations = []
    broad_recommendations = []
    external_recommendations = []

    if has_local_data:
        for drug in all_drugs:
            drug_name = drug['name']
            if drug_name not in sensitivity_map:
                continue
            sensitivity = sensitivity_map[drug_name]

            if data.pregnancy and not drug['pregnancy_safe']:
                continue
            if data.allergy and data.allergy.lower() in drug['class'].lower():
                continue

            is_guideline_match = drug_name in guideline_drugs
            line_bonus = get_drug_line_bonus(data.disease, drug_name)

            if sensitivity >= 50:
                score = calculate_drug_score(drug, sensitivity, data.disease, is_guideline_match)
                rationale = build_rationale(drug, sensitivity, data, is_guideline_match, has_local_data, line_bonus)
                dose_display = get_dose_string(drug, data)
                strict_recommendations.append({
                    "drug_name": drug_name,
                    "aware": drug['aware_category'],
                    "sensitivity": f"{sensitivity}%",
                    "dose_info": dose_display,
                    "rationale": rationale,
                    "class": drug['class'],
                    "score": score,
                    "spectrum": drug['spectrum']
                })
            elif sensitivity >= 30:
                score = calculate_drug_score(drug, sensitivity, data.disease, is_guideline_match)
                rationale = build_rationale(drug, sensitivity, data, is_guideline_match, has_local_data, line_bonus, is_broadened=True)
                dose_display = get_dose_string(drug, data)
                broad_recommendations.append({
                    "drug_name": drug_name,
                    "aware": drug['aware_category'],
                    "sensitivity": f"{sensitivity}% (reduced)",
                    "dose_info": dose_display,
                    "rationale": rationale,
                    "class": drug['class'],
                    "score": score,
                    "spectrum": drug['spectrum']
                })
    else:
        # No local data: try global guidelines first
        for drug in all_drugs:
            if drug['name'] in guideline_drugs:
                if data.pregnancy and not drug['pregnancy_safe']:
                    continue
                if data.allergy and data.allergy.lower() in drug['class'].lower():
                    continue
                dose_display = get_dose_string(drug, data)
                line_bonus = get_drug_line_bonus(data.disease, drug['name'])
                rationale = build_rationale(drug, None, data, True, False, line_bonus)
                strict_recommendations.append({
                    "drug_name": drug['name'],
                    "aware": drug['aware_category'],
                    "sensitivity": "N/A (Global Guideline)",
                    "dose_info": dose_display,
                    "rationale": rationale,
                    "class": drug['class'],
                    "score": 100 + line_bonus,
                    "spectrum": drug['spectrum']
                })

    # If still no recommendations, try external API
    if not strict_recommendations and not broad_recommendations:
        external_drugs = external_api.search_external_guidelines(data.disease, data.microorganism)
        for ext in external_drugs:
            if data.pregnancy:
                # Ideally check pregnancy safety; here we trust external source
                pass
            if data.allergy and data.allergy.lower() in ext.get('class', '').lower():
                continue

            drug_info = {
                "name": ext['drug_name'],
                "aware_category": ext['aware_category'],
                "spectrum": ext['spectrum'],
                "class": ext.get('class', 'Unknown')
            }
            score = calculate_drug_score(drug_info, None, data.disease, is_guideline_match=False,
                                         external_score_modifier=ext.get('score_modifier', 10))
            rationale = build_rationale(drug_info, None, data, False, False, 0,
                                        external_source=ext.get('source', 'External guideline'))
            dose_display = f"{ext['standard_dose']} for {ext['duration']}"
            external_recommendations.append({
                "drug_name": ext['drug_name'],
                "aware": ext['aware_category'],
                "sensitivity": "N/A (External Guideline)",
                "dose_info": dose_display,
                "rationale": rationale + f" – {ext['rationale']}",
                "class": ext.get('class', 'Unknown'),
                "score": score,
                "spectrum": ext['spectrum']
            })

    # Combine all recommendations and deduplicate
    combined_dict = {}
    for rec in strict_recommendations + broad_recommendations + external_recommendations:
        drug_name = rec['drug_name']
        if drug_name not in combined_dict or rec['score'] > combined_dict[drug_name]['score']:
            combined_dict[drug_name] = rec
        elif rec['score'] == combined_dict[drug_name]['score']:
            def extract_sens(s):
                if s in ("N/A (Global Guideline)", "N/A (External Guideline)", "Unknown (Empiric)"):
                    return -1
                try:
                    return float(s.replace('%', '').replace('(reduced)', '').strip())
                except:
                    return -1
            if extract_sens(rec['sensitivity']) > extract_sens(combined_dict[drug_name]['sensitivity']):
                combined_dict[drug_name] = rec

    combined = list(combined_dict.values())

    # If still no recommendations, add a single empiric Access drug as a last resort
    if not combined:
        # Find a safe empiric Access drug
        for drug in all_drugs:
            if drug['aware_category'] == 'Access':
                if data.pregnancy and not drug['pregnancy_safe']:
                    continue
                if data.allergy and data.allergy.lower() in drug['class'].lower():
                    continue
                dose_display = get_dose_string(drug, data)
                rationale = f"Empiric Access antibiotic – {drug['spectrum']} spectrum. No other data available."
                combined.append({
                    "drug_name": drug['name'],
                    "aware": "Access",
                    "sensitivity": "Unknown (Empiric)",
                    "dose_info": dose_display,
                    "rationale": rationale,
                    "class": drug['class'],
                    "score": 20,
                    "spectrum": drug['spectrum']
                })
                break

    if not combined:
        return {
            "primary_recommendation": {
                "recommended": "Consult Specialist",
                "dose": "N/A",
                "sensitivity": "N/A",
                "aware": "N/A",
                "rationale": "No suitable antibiotics found"
            },
            "other_options": []
        }

    # Sort by score descending
    combined.sort(key=lambda x: (-x['score'], x['drug_name']))

    top_rec = combined[0]
    others = combined[1:]

    # Add comparison notes for alternatives
    for alt in others:
        if alt['sensitivity'] not in ("N/A (Global Guideline)", "N/A (External Guideline)", "Unknown (Empiric)") and '%' in alt['sensitivity']:
            try:
                sens_val = float(alt['sensitivity'].replace('%', '').replace('(reduced)', '').strip())
                top_sens_val = float(top_rec['sensitivity'].replace('%', '').replace('(reduced)', '').strip())
                if sens_val < top_sens_val:
                    alt['rationale'] = f"Lower sensitivity ({alt['sensitivity']}) – " + alt['rationale']
            except:
                pass
        if alt.get('spectrum') == 'Broad' and top_rec.get('spectrum') == 'Narrow':
            alt['rationale'] = "Broader spectrum than first choice – " + alt['rationale']

    return {
        "primary_recommendation": {
            "recommended": top_rec['drug_name'],
            "dose": top_rec['dose_info'],
            "sensitivity": top_rec['sensitivity'],
            "aware": top_rec['aware'],
            "rationale": top_rec['rationale']
        },
        "other_options": others
    }

@app.post("/api/save_patient")
def save_patient(data: PatientSaveData):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO patients 
        (disease, microorganism, location, age, sex, pregnancy, allergy, crcl, lfts,
         recommended_drug, dose, sensitivity, aware, rationale)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.disease, data.microorganism, data.location, data.age, data.sex,
        data.pregnancy, data.allergy, data.crcl, data.lfts,
        data.recommended_drug, data.dose, data.sensitivity, data.aware, data.rationale
    ))
    conn.commit()
    patient_id = c.lastrowid
    conn.close()
    return {"message": "Patient data saved", "id": patient_id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)