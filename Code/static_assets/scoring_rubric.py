qual_scoring_rubric = {"qual_rules":[
        {"score": 1, "value": "NOT_SPECIFIED"},
        {"score": 1, "value": "NO"},
        {"score": 2, "value": "CONDITIONAL"},
        {"score": 3, "value": "YES"}]}


quant_scoring_rubric = {
    "Q10": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "unit": "count"},
        {"score": 3, "min": 0, "unit": "count"}
    ],
    "Q18": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "max": 4000000, "unit": "USD"},
        {"score": 3, "min": 4000000, "unit": "USD"}
    ],
    "Q19": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "max": 36, "unit": "months"},
        {"score": 3, "min": 36, "unit": "months"}
    ],
    "Q26": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 12, "max": 24, "unit": "months"},
        {"score": 3, "min": 24, "unit": "months"}
    ],
    "Q29": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 84, "max": 120, "unit": "months"}, 
        {"score": 3, "min": 120, "unit": "months"}
    ],
    "Q3": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "unit": "count"},
        {"score": 3, "min": 0, "unit": "count"}
    ],
    "Q34": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 3, "max": 6, "unit": "months"},
        {"score": 3, "min": 6, "unit": "months"}
    ],
    "Q35": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 3, "max": 5, "unit": "%"},
        {"score": 3, "min": 5, "unit": "%"}
    ],
    "Q38": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 12, "max": 24, "unit": "months"},
        {"score": 3, "min": 24, "unit": "months"}
    ],
    "Q39": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 12, "max": 24, "unit": "months"},
        {"score": 3, "min": 24, "unit": "months"}
    ],
    "Q4": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 9, "unit": "weeks"},  
        {"score": 3, "max": 8, "unit": "weeks"}
    ],
    "Q40": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 12, "max": 24, "unit": "months"},
        {"score": 3, "min": 24, "unit": "months"}
    ],
    "Q47": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 85, "max": 90, "unit": "%"},
        {"score": 3, "min": 90, "unit": "%"}
    ],
    "Q49": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "max": 60, "unit": "days"},
        {"score": 3, "min": 60, "unit": "days"}
    ],
    "Q9": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "max": 12, "unit": "months"},
        {"score": 3, "min": 12, "unit": "months"}
    ]
}

quant_scoring_rubric_v1 = {
    "Q10": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "unit": "count"},
        {"score": 3, "min": 0, "unit": "count"}
    ],
    "Q18": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "unit": "count"},
        {"score": 3, "min": 0, "unit": "count"}
    ],
    "Q19": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "max": 3, "unit": "years"},
        {"score": 3, "min": 3, "unit": "years"}
    ],
    "Q26": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 3, "max": 6, "unit": "months"},
        {"score": 3, "min": 12, "unit": "months"}
    ],
    "Q29": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 7, "max": 12, "unit": "years"}, 
        {"score": 3, "min": 12, "unit": "years"}
    ],
    "Q3": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 0, "unit": "count"},
        {"score": 3, "min": 0, "unit": "count"}
    ],
    "Q34": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 3, "max": 6, "unit": "months"},
        {"score": 3, "min": 6, "unit": "months"}
    ],
    "Q35": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 1, "max": 3, "unit": "%"},
        {"score": 3, "min": 3, "unit": "%"}
    ],
    "Q38": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 12, "max": 24, "unit": "months"},
        {"score": 3, "min": 24, "unit": "months"}
    ],
    "Q39": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 12, "max": 24, "unit": "months"},
        {"score": 3, "min": 24, "unit": "months"}
    ],
    "Q4": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 9, "unit": "weeks"},  
        {"score": 3, "max": 8, "unit": "weeks"}
    ],
    "Q40": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 12, "max": 24, "unit": "months"},
        {"score": 3, "min": 24, "unit": "months"}
    ],
    "Q47": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "min": 85, "max": 90, "unit": "%"},
        {"score": 3, "min": 90, "unit": "%"}
    ],
    "Q49": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "max": 60, "unit": "days"},
        {"score": 3, "min": 60, "unit": "days"}
    ],
    "Q9": [
        {"score": 1, "rule": "missing"},
        {"score": 2, "max": 12, "unit": "months"},
        {"score": 3, "min": 12, "unit": "months"}
    ]
}
