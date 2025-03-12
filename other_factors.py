import json
def other_factors():
    result=[{"factors": "F1","value": 1,"rationale": "Based on the selection of human therapeutic dose."},
            {"factors": "F2","value": 10,"rationale": "Conventionally used to allow for differences between individuals in the human population."},
            {"factors": "F6","value": 1,"rationale": "Generic drugs and non-clinical data available"},
            {"factors": "α","value": 1,"rationale": "No pharmacokinetic correction is carried out for PDE calculation since the same route of administration is used."}]
    return json.dumps(result, ensure_ascii=False)
if __name__ == "__main__":
    print(other_factors())

