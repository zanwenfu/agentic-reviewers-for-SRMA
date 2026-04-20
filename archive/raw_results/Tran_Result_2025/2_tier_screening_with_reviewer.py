import ast
import re
import os
import time
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llms.chatgpt import gpt_4o_mini, gpt_o3_mini
from dataset.PICOS_data import title, abstract, objective, method

cost = 0

def construct_prompt_classifier(SR_title, SR_abstract, candidate_title, candidate_abstract):
    ask_chatgpt = "### Systematic Review: Title, Abstract and Keywords\n"
    ask_chatgpt += f"**Title:** \n{SR_title}\n"
    ask_chatgpt += f"**Abstract:** \n{SR_abstract}\n"

    ask_chatgpt += "### Citation in investigation\n"
    ask_chatgpt += f"I give the title and abstract of the article that is in investigation as input.\n"
    ask_chatgpt += f"**Title:** {candidate_title}\n"
    ask_chatgpt += f"**Abstract:** {candidate_abstract}\n\n"

    ask_chatgpt += "### Instructions, including abstract considerations\n"
    ask_chatgpt += "We now evaluate the relevance of provided article, and categorize it into one of the broad categories: potentially relevant, likely irrelevant, and uncertain.\n"
    ask_chatgpt += "First, we will reflect on the contents of both systematic review and article in investigation. Then we will think step by step, giving reasons for why the articles are categorized as potentially relevant, likely irrelevant, or uncertain.\n"

    ask_chatgpt += "\n### Importance\n"
    ask_chatgpt += "Be lenient. Our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant.\n"
    ask_chatgpt += "### Output format\n"
    ask_chatgpt += "We will conclude by outputting (on the very last line) 'XXX', if the study is potentially relevant. 'YYY', if the study is uncertain. 'ZZZ', if the study is likely irrelevant.\n"

    return ask_chatgpt

def classifier(SR_title, SR_abstract, candidate_title, candidate_abstract):
    global cost
    while True:
        ask_chatgpt = construct_prompt_classifier(SR_title, SR_abstract, candidate_title, candidate_abstract)

        justification, curr_cost = gpt_4o_mini(ask_chatgpt, "classifier")
        cost += curr_cost
        print(justification)
        if re.search("XXX", justification, re.IGNORECASE):
            decision = "potentially relevant"
        elif re.search("YYY", justification, re.IGNORECASE):
            decision = "uncertain"
        elif re.search("ZZZ", justification, re.IGNORECASE):
            decision = "likely irrelevant"
        else:
            continue

        return justification, decision


def classifier_reviewer(SR_title, SR_abstract, CA_title, CA_abstract, decision, Justification):
    raw_prompt = f"""
### Systematic Review: Title, Abstract
    
- **Title of Systematic Reivew**:
{SR_title}

- **Abstract of Systematic Review**:
{SR_abstract}

### Candidate article that is being evaluated for the systematic review: Title, Abstract

- **Title of the candidate article**:
{CA_title}

- **Abstract of the candidate article**:
{CA_abstract}

### Decision from another medical researcher
Another medical researcher has decided the candidate article to be {decision}, and written the following justification for it.
{Justification}

### Instructions
Your task is to evaluate the justification this medical researcher has given, and decide whether the decision it made is correct or wrong.

### Output format
We will conclude by outputting (on the very last line) 'XXX' if you agree with the medical researcher, or 'YYY' if you disagree with it. We must output either 'XXX' or 'YYY'.
"""
    global cost
    while True:
        evaluation, curr_cost = gpt_o3_mini(raw_prompt, "classifier reviewer")
        cost += curr_cost
        print(evaluation)
        if re.search("XXX", evaluation, re.IGNORECASE):
            decision = True
        elif re.search("YYY", evaluation, re.IGNORECASE):
            decision = False
        else:
            continue

        return evaluation, decision

def classifier_improver(SR_title, SR_abstract, CA_title, CA_abstract, feedback):
    raw_prompt = construct_prompt_classifier(SR_title, SR_abstract, CA_title, CA_abstract)
    msg_thread = []
    msg_thread.append({"role": "system", "content": (
        "You are an experienced medical researcher specializing in systematic reviews."
        "You are assisting in a medical systematic review and are tasked with screening and categorizing articles based on their relevance."
    )
    })
    msg_thread.append({"role": "user", "content":
f"""
### Original prompt
{raw_prompt}

### Feedback from reviewer
{feedback}

### Instructions
Another experienced medical researcher has decided that your justification for the candidate article is incorrect.
Re-evaluate the relevance of the candidate article based on the feedback.
We will conclude by outputting (on the very last line) 'XXX', if the study is potentially relevant. 'YYY', if the study is uncertain. 'ZZZ', if the study is likely irrelevant.
"""})
    global cost
    while True:
        improver_resp, curr_cost = gpt_4o_mini(msg_thread)
        cost += curr_cost
        print(improver_resp)
        if re.search("XXX", improver_resp, re.IGNORECASE):
            decision = "potentially relevant"
        elif re.search("YYY", improver_resp, re.IGNORECASE):
            decision = "uncertain"
        elif re.search("ZZZ", improver_resp, re.IGNORECASE):
            decision = "likely irrelevant"
        else:
            continue
        
        return improver_resp, decision



def classifier_execute(idx_list):

    for idx in idx_list:
        output_file = open(f"Tran_Result_2025\\Sbidian{idx}_gpt1.txt", "a", encoding="utf-8")

        SR_title = title[2]
        SR_abstract = abstract[2]
        total_disagreements = 0

        data_file = open(f"data\\PICOS\\Sbidian{idx}.txt", "r", encoding="utf-8")
        data = data_file.readlines()

        for line in data:
            curr_title = line.split("$$$")[0].strip()
            curr_abstract = line.split("$$$")[1].strip()

            success = False
            classifier_resp, decision = classifier(SR_title, SR_abstract, curr_title, curr_abstract)
            while not success:
                reviewer_resp, success = classifier_reviewer(SR_title, SR_abstract, curr_title, curr_abstract, decision, classifier_resp)
                if not success:
                    total_disagreements += 1
                    classifier_resp, decision = classifier_improver(SR_title, SR_abstract, curr_title, curr_abstract, reviewer_resp)

            if decision in ["potentially relevant", "uncertain"]:
                output_file.write(curr_title+"$$$ "+curr_abstract+"\n")

        print(f"Total disagreements: {total_disagreements}")
        output_file.write(f"Total disagreements: {total_disagreements}\n")
        output_file.write("Cost: " + str(cost) + "\n")


def construct_prompt_detailed_screener(SR_title, SR_abstract, SR_objective, SR_method, candidate_title, candidate_abstract):
    PICOS_prompt = "### Systematic Review: Title, Abstract\n"
    PICOS_prompt += f"**Title:** {SR_title}\n"
    PICOS_prompt += f"**Abstract:** {SR_abstract}\n"
    
    PICOS_prompt += "### Pre-prompt, including objectives and methodologies\n"
    PICOS_prompt += "Our systematic review is governed by the following objectives and methodologies:\n"

    PICOS_prompt += "**Objectives:**\n"
    PICOS_prompt += f"{SR_objective}\n\n"
    PICOS_prompt += "**Methodologies:**\n"
    PICOS_prompt += f"{SR_method}\n\n"

    PICOS_prompt += "\n### Citation in investigation\nI give the title and abstract of the article that is in investigation as input.\n"
    PICOS_prompt += f"**Title:** {candidate_title}\n"
    PICOS_prompt += f"**Abstract:** {candidate_abstract}\n\n"

    PICOS_prompt += "### Instructions, including abstract considerations\n"
    PICOS_prompt += "We now assess whether the article should be included in the systematic review by evaluating the contents from 5 perspectives: Population, Intervention, Control, Outcomes and Study Design (PICOS).\n"
    PICOS_prompt += "Some example criteria for reference, but not limited to:\n"
    PICOS_prompt += "- **Population:** Does the study focus on the specific patient population relevant to this review (e.g., age group, medical condition, gender, or clinical status)?\n"
    PICOS_prompt += "- **Intervention:** Does the article investigate the medical intervention of interest (e.g., a specific drug, surgical procedure, lifestyle intervention, or medical device)?\n"
    PICOS_prompt += "- **Comparison:** Does the study compare the intervention to an appropriate control (e.g., placebo, no treatment, standard care, or an alternative treatment)?\n"
    PICOS_prompt += "- **Outcome:** Are the outcomes measured in the study relevant to the review (e.g., clinical outcomes, mortality rates, disease progression, quality of life)?\n"
    PICOS_prompt += "- **Study Design:** Is the study design appropriate for answering the research question (e.g., randomized controlled trials, cohort studies, case-control studies)?\n\n"
    
    PICOS_prompt += "### Tasks:\n"
    PICOS_prompt += "First, always remember to reflect on the contents of both systematic review and article in investigation. Then, we will think step by step for each perspective, giving reasons for why or why not the article in investigation align with our systematic review.\n"
    PICOS_prompt += "\n### Importances\n"
    PICOS_prompt += "Be lenient. Studies that may not fully align with the primary focus of our inclusion criteria but provide data or insights potentially relevant to our review deserve thoughtful consideration. Given the nature of abstracts as concise summaries of comprehensive research, some degree of interpretation is necessary.\n"

    # PICOS_prompt += "Most importantly, our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant.\n"
    
    PICOS_prompt += "\n### Output format\n"
    PICOS_prompt += "We will conclude by outputting (on the very last line) 'XXX' if the article warrants exclusion, or 'YYY' if inclusion is advised or uncertainty persists. We must output either 'XXX' or 'YYY'.\n"

    return PICOS_prompt

def detailed_citation_screening(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract):
    global cost
    PICOS_prompt = construct_prompt_detailed_screener(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract)
    while True:
        gpt_ans, curr_cost = gpt_4o_mini(PICOS_prompt, "detailed screener")
        cost += curr_cost
        print(gpt_ans)
        if re.search("YYY", gpt_ans, re.IGNORECASE):
            decision = "included"
        elif re.search("XXX", gpt_ans, re.IGNORECASE):
            decision = "excluded"
        else:
            continue
        return gpt_ans, decision
    
def detailed_citation_reviewer(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract, decision, Justification):
    raw_prompt = f"""
### Systematic Review: Title, Abstract, Objectives and Methodologies
**Title of Systematic Reivew**:
{SR_title}

**Abstract of Systematic Review**:
{SR_abstract}

**Objective of the Systematic Review**:
{SR_objective}

**Methodology of the Systematic Review**:
{SR_method}

### Candidate article that is being evaluated for the systematic review: Title, Abstract
**Title of the candidate article**:
{CA_title}

**Abstract of the candidate article**:
{CA_abstract}

### Decision from another medical researcher
Another medical researcher has decided the candidate article to be {decision}, and written the following justification for it.
{Justification}

### Instructions
Your task is to evaluate the justification this medical researcher has given, and decide whether the decision it made is correct or wrong.

### Output format
We will conclude by outputting (on the very last line) 'XXX' if you agree with the medical researcher, or 'YYY' if you disagree with it. We must output either 'XXX' or 'YYY'.
"""
    global cost
    while True:
        evaluation, curr_cost = gpt_o3_mini(raw_prompt, "detailed screener reviewer")
        cost += curr_cost
        print(evaluation)
        if re.search("XXX", evaluation, re.IGNORECASE):
            decision = True
        elif re.search("YYY", evaluation, re.IGNORECASE):
            decision = False
        else:
            continue

        return evaluation, decision

def detailed_citation_improver(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract, feedback):
    raw_prompt = construct_prompt_detailed_screener(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract)
    msg_thread = []
    msg_thread.append({"role": "system", "content": (
        "You are an experienced medical researcher specializing in systematic reviews."
        "You are assisting in a medical systematic review and are tasked with screening and deciding whether articles should be included in our systematic review based on their relevance."
    )
    })
    msg_thread.append({"role": "user", "content":
f"""
### Original prompt
{raw_prompt}

### Feedback from reviewer
{feedback}

### Instructions
Another experienced medical researcher has decided that your justification for the candidate article is incorrect.
Re-evaluate the relevance of the candidate article based on the feedback.
We will conclude by outputting (on the very last line) 'XXX' if the article warrants exclusion, or 'YYY' if inclusion is advised or uncertainty persists. We must output either 'XXX' or 'YYY'.
"""})
    global cost
    while True:
        improver_resp, curr_cost = gpt_4o_mini(msg_thread)
        cost += curr_cost
        print(improver_resp)
        if re.search("XXX", improver_resp, re.IGNORECASE):
            decision = "excluded"
        elif re.search("YYY", improver_resp, re.IGNORECASE):
            decision = "included"
        else:
            continue
        
        return improver_resp, decision


def detailed_citation_execute(idx_list):

    for idx in idx_list:
        data_file = open(f"Tran_Result_2025\\Sbidian{idx}_gpt1.txt", "r", encoding="utf-8")
        output_file = open(f"Tran_Result_2025\\Sbidian{idx}_gpt2.txt", "w+", encoding="utf-8")

        data = data_file.readlines()

        SR_title = title[2]
        SR_abstract = abstract[2]
        SR_objective = objective[2]
        SR_method = method[2]
        total_disagreements = 0
        
        for line in data:
            try:
                curr_title = line.split("$$$")[0].strip()
                curr_abstract = line.split("$$$")[1].strip()
            except:
                continue

            success = False
            detailed_screener_resp, decision = detailed_citation_screening(SR_title, SR_abstract, SR_objective, SR_method, curr_title, curr_abstract)
            while not success:
                reviewer_resp, success = detailed_citation_reviewer(SR_title, SR_abstract, SR_objective, SR_method, curr_title, curr_abstract, decision, detailed_screener_resp)
                if not success:
                    total_disagreements += 1
                    detailed_screener_resp, decision = detailed_citation_improver(SR_title, SR_abstract, SR_objective, SR_method, curr_title, curr_abstract, reviewer_resp)

            if decision == "included":
                output_file.write(curr_title+"$$$ "+curr_abstract+"\n")

        print(f"Total disagreements: {total_disagreements}")
        output_file.write(f"Total disagreements: {total_disagreements}\n")
        output_file.write("Cost: " + str(cost) + "\n")



def execute():
    idx_list = [1, 2]
    classifier_execute(idx_list)
    detailed_citation_execute(idx_list)


if __name__ == '__main__':
    start_time = time.time()
    execute()
    end_time = time.time()
    duration = end_time - start_time
    print(f"Execution time: {duration} seconds")
    print(f"Execution time: {duration/60} minutes")
    print(f"Execution time: {duration/3600} hours")

    print(f"Total cost: {cost} USD")

