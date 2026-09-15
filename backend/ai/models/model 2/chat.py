# chat.py

from assistant import admin_query_handler

def handle_admin_message(
    session,
    user_message,
    ml1_output,
    evidence
):
    session.log("admin", user_message)

    reply = admin_query_handler(
        query=user_message,
        case_id=session.case_id,
        ml1_output=ml1_output,
        evidence=evidence
    )

    session.log("ml2", reply)
    return reply
