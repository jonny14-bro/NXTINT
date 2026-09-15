# assistant.py

from intent import detect_intents
from context import build_context
from reasoning import reason
from responses import format_response

def admin_query_handler(
    query,
    case_id,
    ml1_output,
    evidence,
    compare_cases_data=None
):
    intents = detect_intents(query)
    context = build_context(case_id, ml1_output, evidence)

    if compare_cases_data:
        context.update(compare_cases_data)

    responses = []

    for intent in intents:
        reasoning_result = reason(intent, context)
        formatted = format_response(reasoning_result)
        responses.append(formatted)

    return "\n\n".join(responses)
