import ast
import re
import os
from openai import OpenAI
import time
import json

from data import all_titles_LR, all_abstracts_LR, all_objectives_LR, all_methods_LR, all_included_articles_LR


def try_gpt_4(message):
    # NOTE: this file is preserved under archive/ for provenance only.
    # The original hard-coded key was revoked and redacted before open-sourcing.
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    while True:
        try:
            response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={ "type": "text" },
                    messages=message,
                    temperature=0.0,
                    timeout = 20
                )
            # print(response.choices[0].message.content)
            return response.choices[0].message.content
        except:
            time.sleep(10)
            print("The request timed out.")


def extract_PICOS(title, abstract, objective, method):
    data = {
        "Population": "xxx",
        "Intervention": "xxx",
        "Comparison": "xxx",
        "Outcomes": "xxx",
        "Study Design": "xxx"
    }

    prompt = f"""
You are an AI assistant for medical research conducting article screening for inclusion in a systematic review.

### title:
{title}

### abstract:
{abstract}

### objective:
{objective}

### method:
{method}

Based on the information as above, identify the Population, Intervention, Comparison, Outcomes, and Study Design of it.
Finally give me your answer in JSON format:
{json.dumps(data, indent=4)}
    """
    msg_thread = [{"role": "user", "content": prompt}]

    while True:
        try:
            model_resp = try_gpt_4(msg_thread)
            # print(model_resp)
            json_start_index = model_resp.find("{")
            json_end_index = model_resp.rfind("}") + 1  # Find the last closing brace
            json_string = model_resp[json_start_index:json_end_index]
            print(json_string)
            PICOS = json.loads(json_string)
            return PICOS["Population"], PICOS["Intervention"], PICOS["Comparison"], PICOS["Outcomes"], PICOS["Study Design"]
        except:
            continue
    


def search_type_and_year(candidate_title, candidate_abstract):
    data = {
        "Reference Type": "xxx",
        "Publication Year": "xxx"
    }

    prompt = f"""
### Title
{candidate_title}

### Abstract
{candidate_abstract}

Now based on the information as above, identify the reference type and publication year of it. If you cannot identify the publication year directly, carefully analyze the context and give me the closest publication year you think.
Finally give me your answer in JSON format:
{json.dumps(data, indent=4)}
"""
    msg_thread = [{"role": "user", "content": prompt}]
    while True:
        model_resp = try_gpt_4(msg_thread)
        print(model_resp)
        json_start_index = model_resp.find("{")
        json_end_index = model_resp.rfind("}") + 1  # Find the last closing brace
        json_string = model_resp[json_start_index:json_end_index]
        try:
            type_year = json.loads(json_string)
            return type_year["Reference Type"], type_year["Publication Year"]
        except:
            continue

def construct_prompt(candidate_title, candidate_abstract, reference_type, publication_year,
                     population, intervention, comparison, outcomes, study_design):
    msg_thread = []
    msg_thread.append({"role": "system", "content": "Role: You are an AI assistant for medical research conducting article screening for inclusion in a systematic review."})
    msg_thread.append({"role": "user", "content": """Task: You are given an article and PICOS in JSON format. Your response must be concise and in JSON format containing these key/values:
                       answer: [how the article is or is not relevant to the PICOS],
                       rating: [relevance rating number in integer from ranging from 1 (least relevance) to 5 (most relevance)]"""})
    msg_thread.append({"role": "user", "content": f"""
                       Article:
                       Title: {candidate_title}
                       Abstract: {candidate_abstract}
                       Reference type: {reference_type}
                       Published year: {publication_year}"""})
    msg_thread.append({"role": "user", "content": f"""
                       PICOS:
                       Population: {population},
                       Intervention: {intervention},
                       Comparison: {comparison},
                       Outcomes: {outcomes},
                       Study Design: {study_design}"""})

    while True:
        model_resp = try_gpt_4(msg_thread)
        print(model_resp)
        json_start_index = model_resp.find("{")
        json_end_index = model_resp.rfind("}") + 1  # Find the last closing brace
        json_string = model_resp[json_start_index:json_end_index]
        try:
            answer_JSON = json.loads(json_string)
            return answer_JSON["rating"]
        except:
            continue
    

def execute():
    directory = "literature_review\\dataset"

    for idx in range(1, 9):
        data_file_paths = [f for f in os.listdir(directory) if f.startswith(str(idx+1)+"_")]
        print(data_file_paths)
        output_file = open(f"literature_review\\LR_2_result\\gpt_{idx+1}.txt", "w+", encoding="utf-8")

        print(all_titles_LR.titles[idx])
        curr_included_articles = [x.lower() for x in all_included_articles_LR.included_articles[idx+1]]

        P, I, C, O, S = extract_PICOS(all_titles_LR.titles[idx], all_abstracts_LR.abstracts[idx], all_objectives_LR.objectives[idx], all_methods_LR.methods[idx])

        total = 0
        total_filtered = 0
        FP_set = set()
        TP_set = set()
        FN_set = set()
        TN_set = set()
        
        for path in data_file_paths:
            data_file = open(f"{directory}\\{path}", "r", encoding="utf-8")
            data = data_file.readlines()
            total += len(data)
            
            for line in data:
                curr_title = line.split(";")[0].strip()
                curr_abstract = line.split(";")[1].strip()

                _type, year = search_type_and_year(curr_title, curr_abstract)
                rating = construct_prompt(curr_title, curr_abstract, _type, year, P, I, C, O, S)

                if int(rating) >= 3:
                    output_file.write(curr_title+"; "+curr_abstract+"\n")
                    total_filtered += 1

                    # Add to TP
                    if curr_title.lower() in curr_included_articles or curr_title.lower()+"." in curr_included_articles or curr_title.lower()[:-1] in curr_included_articles:
                        if curr_title.endswith("."):
                            TP_set.add(curr_title.lower())
                        else:
                            TP_set.add(curr_title.lower()+".")

                    # Add to FP
                    if curr_title.endswith("."):
                        FP_set.add(curr_title.lower())
                    else:
                        FP_set.add(curr_title.lower()+".")

                else:
                    # Add to FN
                    if curr_title.lower() in curr_included_articles or curr_title.lower()+"." in curr_included_articles or curr_title.lower()[:-1] in curr_included_articles:
                        if curr_title.endswith("."):
                            FN_set.add(curr_title.lower())
                        else:
                            FN_set.add(curr_title.lower()+".")

                    # Add to TN
                    else:
                        if curr_title.endswith("."):
                            TN_set.add(curr_title.lower())
                        else:
                            TN_set.add(curr_title.lower()+".")

        FP = len(FP_set)
        FN = len(FN_set)
        TP = len(TP_set)
        TN = len(TN_set)

        FP_rate = FP / (FP + TN)
        Specificity_rate = TN / (FP + TN)
        FN_rate = FN / (FN + TP)   
        Sensitivity_rate = TP / (FN + TP)

        output_file.write(
            f"""

total: {total}   FP: {FP}   FN: {FN}   TP: {TP}   TN: {TN}

FP Rate: {FP_rate}   FN Rate: {FN_rate}   Specificity: {Specificity_rate}   Sensitivity: {Sensitivity_rate}  

"""
        )



if __name__ == '__main__':
    execute()
