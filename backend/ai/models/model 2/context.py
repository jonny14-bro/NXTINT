# context.py

def build_context(case_id, ml1_output, evidence):
    return {
        "case_id": case_id,
        "decision": ml1_output["decision"],
        "confidence": ml1_output["confidence"],
        "confidence_level": ml1_output["confidence_level"],
        "explanation": ml1_output["explanation"],
        "evidence": evidence
    }
