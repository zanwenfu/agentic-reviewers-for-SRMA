import ast
import re
import os
from openai import OpenAI
import time

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
                messages=[
                    {"role": "user", "content": message}
                    ],
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



def  construct_prompt(SR_title, candidate_title, candidate_abstract, inclusion_criteria, exclusion_criteria):
    prompt = f"""
Conduct a systematic review on {SR_title}.
I provide the title and abstract for one journal article. Provide an overall assessment based on eligibility criteria with only one word answer yes or no, with no explanation. Then, for each inclusion or exclusion criterion, answer with only one word, yes if it is included by the inclusion criterion or excluded by the exclusion criterion, and answer no if it does not meet the inclusion criterion or not excluded by the exclusion criterion. After answering all the criteria with yes or no, then provide an overall explanation.
Here is the eligibility criteria: 
Inclusion Criteria:
{inclusion_criteria}
Exclusion Criteria:
{exclusion_criteria}

Here is the title:
{candidate_title}
Here is the abstract:
{candidate_abstract}
   
In the end, if you think the article should be considered in my systematic review, output \'XXX\' at the last line. Otherwise, output \'YYY\' at the last line.
    """

    # print(prompt)

    while True:
        model_resp = try_gpt_4(prompt)
        # print(model_resp)
        if re.search("XXX", model_resp, re.IGNORECASE):
            return True
        if re.search("YYY", model_resp, re.IGNORECASE):
            return False
    

def execute():
    directory = "literature_review\\dataset"

    for idx in range(9, 16):
        data_file_paths = [f for f in os.listdir(directory) if f.startswith(str(idx+1)+"_")]
        print(data_file_paths)
        output_file = open(f"literature_review\\result\\gpt_{idx+1}.txt", "w+", encoding="utf-8")

        inclusion_criteria = generate_criteria(all_titles_LR.titles[idx], 
                                               all_abstracts_LR.abstracts[idx],
                                               all_objectives_LR.objectives[idx],
                                               all_methods_LR.methods[idx],
                                               "inclusion")
        
        exclusion_criteria = generate_criteria(all_titles_LR.titles[idx], 
                                               all_abstracts_LR.abstracts[idx],
                                               all_objectives_LR.objectives[idx],
                                               all_methods_LR.methods[idx],
                                               "exclusion")
        
        print(all_titles_LR.titles[idx])
        print(inclusion_criteria)
        print(exclusion_criteria)

        curr_results_without_duplicates = set()
        total = 0
        TP_set = set()
        FN_set = set()
        curr_included_articles = [x.lower() for x in all_included_articles_LR.included_articles[idx+1]]

        for path in data_file_paths:
            data_file = open(f"{directory}\\{path}", "r", encoding="utf-8")
            data = data_file.readlines()
            total += len(data)
            
            for line in data:
                curr_title = line.split(";")[0].strip()
                curr_abstract = line.split(";")[1].strip()

                success = construct_prompt(all_titles_LR.titles[idx], curr_title, curr_abstract, inclusion_criteria, exclusion_criteria)
                if success:
                    if curr_title.lower() in curr_included_articles or curr_title.lower()+"." in curr_included_articles or curr_title.lower()[:-1] in curr_included_articles:
                        TP_set.add(curr_title.lower())

                    if curr_title.lower() not in curr_results_without_duplicates:
                        output_file.write(curr_title+"; "+curr_abstract+"\n")
                        curr_results_without_duplicates.add(curr_title.lower())
                else:
                    if curr_title.lower() in curr_included_articles or curr_title.lower()+"." in curr_included_articles or curr_title.lower()[:-1] in curr_included_articles:
                        FN_set.add(curr_title.lower())

        FP = len(curr_results_without_duplicates) - len(TP_set)
        FN = len(FN_set)
        TP = len(TP_set)
        TN = total - FP - FN - TP

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
