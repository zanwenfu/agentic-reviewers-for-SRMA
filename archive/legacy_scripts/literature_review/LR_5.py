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
                    messages=[{"role": "user", "content": message}],
                    temperature=1.0,
                    timeout = 20
                )
            # print(response.choices[0].message.content)
            return response.choices[0].message.content
        except:
            time.sleep(10)
            print("The request timed out.")


def generate_criteria(title, abstract, objective, method, criteria_type):
    prompt = f"""
You are a medical researcher analyzing abstracts for the following systematic review:

### Title
{title}

### Abstract
{abstract}

### objective
{objective}

### method
{method}

Now based on the content as above, generate corresponding {criteria_type} criteria for me to screen articles.
Your answer should follow exactly the format:
1. xxx
2. xxx
3. xxx
    """

    criteria = try_gpt_4(prompt)
    return criteria
    

def construct_prompt(candidate_abstract, SR_objective, inclusion_criteria, exclusion_criteria):
    msg_thread = "{Pre-prompt, including objectives}"
    msg_thread += f"Our systematic review is governed by the following objectives: {SR_objective}\n\n"
    msg_thread += "The following is an excerpt of two sets of criteria. A study is considered included if it meets all the inclusion criteria. lf a study meets any of the exclusion criteria, it should be excluded. Here are the two sets of criteria:\n\n"
    msg_thread += "{Inclusion Criteria}\n"
    msg_thread += inclusion_criteria + "\n"
    msg_thread += "{Exclusion Criteria}\n"
    msg_thread += exclusion_criteria + "\n"
    msg_thread += "{Abstract in investigation}\n"
    msg_thread += candidate_abstract + "\n\n"
    msg_thread += """
{Instructions, including abstract considerations}
# Instructions
We now assess whether the paper should be included from the systematic review by evaluating it against each and every predefined inclusion and exclusion criterion. First, we will reflect on how we will decide whether a paper should be included or excluded. Then, we will think step by step for each criteria, giving reasons for why they are met or not met.
Studies that may not fully align with the primary focus of our inclusion criteria but provide data or insights potentially relevant to our review deserve thoughtful consideration. Given the nature of abstracts as concise summaries of comprehensive research, some degree of interpretation is necessary.

Our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant, We will conclude by outputting (on the very lastline) 'XXX' if the paper warrants exclusion, or 'YYY' if inclusion is advised or uncertainty persists. We must output either 'XXX' or'YYY.

{Model output}
"""

    while True:
        model_resp = try_gpt_4(msg_thread)
        print(model_resp)
        if re.search("XXX", model_resp, re.IGNORECASE):
            return False
        if re.search("YYY", model_resp, re.IGNORECASE):
            return True


def execute():
    directory = "literature_review\\dataset"

    for idx in [3]:
        data_file_paths = [f for f in os.listdir(directory) if f.startswith(str(idx+1)+"_")]
        print(data_file_paths)
        output_file = open(f"literature_review\\LR_5_result\\gpt_{idx+1}.txt", "w+", encoding="utf-8")

        print(all_titles_LR.titles[idx])
        curr_included_articles = [x.lower() for x in all_included_articles_LR.included_articles[idx+1]]

        inclusion_criteria = generate_criteria(all_titles_LR.titles[idx], 
                                               all_abstracts_LR.abstracts[idx],
                                               all_objectives_LR.objectives[idx],
                                               all_methods_LR.methods[idx],
                                               "Inclusion")
        
        exclusion_criteria = generate_criteria(all_titles_LR.titles[idx], 
                                               all_abstracts_LR.abstracts[idx],
                                               all_objectives_LR.objectives[idx],
                                               all_methods_LR.methods[idx],
                                               "Exclusion")

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

                success = construct_prompt(curr_abstract, all_objectives_LR.objectives[idx], inclusion_criteria, exclusion_criteria)

                if success:
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

Inclusion criteria:
{inclusion_criteria}

Exclusion criteria:
{exclusion_criteria}            

total: {total}   FP: {FP}   FN: {FN}   TP: {TP}   TN: {TN}

FP Rate: {FP_rate}   FN Rate: {FN_rate}   Specificity: {Specificity_rate}   Sensitivity: {Sensitivity_rate}  

"""
        )



if __name__ == '__main__':
    execute()
