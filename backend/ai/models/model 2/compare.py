# compare.py

def compare_cases(case_a, case_b):
    diffs = {}

    for key in case_a["evidence"]:
        a = case_a["evidence"][key]
        b = case_b["evidence"][key]

        if a != b:
            diffs[key] = {
                "case_a": a,
                "case_b": b
            }

    return diffs
