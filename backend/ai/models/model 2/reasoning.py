# reasoning.py
from compare import compare_cases
from timeline import build_timeline


def reason(intent, context):
    decision = context["decision"]
    confidence = context["confidence"]
    evidence = context["evidence"]

    if intent == "WHY_DECISION":
        return {
            "type": "explanation",
            "message": context["explanation"]
        }

    if intent == "CONFIDENCE_MEANING":
        return {
            "type": "confidence",
            "message": f"Confidence is {context['confidence_level']} ({confidence:.2f})."
        }

    if intent == "WHAT_EVIDENCE_MISSING":
        missing = []
        if evidence["source_count"] < 3:
            missing.append("More independent sources")
        if evidence["metadata_similarity"] < 0.6:
            missing.append("Stronger metadata correlation")
        if evidence["platform_overlap"] < 2:
            missing.append("Cross-platform confirmation")

        return {
            "type": "gap_analysis",
            "missing": missing
        }

    if intent == "CAN_WE_CONFIRM":
        if decision != "CONFIRMED MATCH":
            return {
                "type": "warning",
                "message": "Insufficient evidence to confirm safely."
            }
    
    if intent == "COMPARE_CASES":
        differences = compare_cases(
            context["case_a"],
            context["case_b"]
        )

        return {
            "type": "comparison",
            "differences": differences
        }
    if intent == "TIMELINE_VIEW":
        sources = context["evidence"].get("sources", [])

        timeline = build_timeline(sources)

        if not timeline:
            return {
                "type": "timeline",
                "message": "No reliable timestamped evidence available."
            }

        return {
            "type": "timeline",
            "events": timeline,
            "first_seen": timeline[0],
            "last_seen": timeline[-1]
        }


    return {
        "type": "risk",
        "message": "Maintain current assessment and gather more evidence."
    }
