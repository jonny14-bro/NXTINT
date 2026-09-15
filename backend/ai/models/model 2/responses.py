# responses.py

def format_response(result):
    if result["type"] == "gap_analysis":
        if not result["missing"]:
            return "No major evidence gaps detected."
        return "Missing evidence:\n- " + "\n- ".join(result["missing"])

    if result["type"] == "warning":
        return f"⚠️ {result['message']}"

    if result["type"] == "confidence":
        return result["message"]

    if result["type"] == "explanation":
        return "Decision rationale:\n" + "\n".join(result["message"])
    
    if result["type"] == "comparison":
        lines = ["Key differences detected:"]
        for k, v in result["differences"].items():
            lines.append(
                f"- {k}: Case A = {v['case_a']} | Case B = {v['case_b']}"
            )
        return "\n".join(lines)
    
    if result["type"] == "timeline":
        if "events" not in result:
            return result["message"]

        lines = []
        lines.append(
            f"First seen: {result['first_seen']['time']} "
            f"in {result['first_seen']['source']} "
            f"(confidence: {result['first_seen']['confidence']})"
        )

        lines.append(
            f"Last seen: {result['last_seen']['time']} "
            f"in {result['last_seen']['source']} "
            f"(confidence: {result['last_seen']['confidence']})"
        )

        lines.append("\nFull timeline:")

        for e in result["events"]:
            lines.append(
                f"- {e['time']} | {e['type']} | {e['source']} | confidence: {e['confidence']}"
            )

        return "\n".join(lines)

    return result["message"]
