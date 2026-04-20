import ast
import re
import os
from fuzzywuzzy import process
from llms.chatgpt import gpt_4o_mini, gpt_o3_mini
from literature_review.data import all_titles_LR, all_abstracts_LR, all_objectives_LR, all_methods_LR, all_included_articles_LR


def retrieve_full_text(full_text_folder, title):
    txt_files = [f for f in os.listdir(full_text_folder) if f.endswith(".txt")]
    txt_file_names = [os.path.splitext(f)[0] for f in txt_files]  # Remove .txt extension

    # Find best match from available file names
    best_match, score = process.extractOne(title, txt_file_names)

    if score > 80:  # Accept only high-confidence matches
        matched_file = best_match + ".txt"  # Add .txt extension
    else:
        return "No match found"

    if matched_file != "No match found":
        full_text_path = os.path.join(full_text_folder, matched_file)
        with open(full_text_path, "r", encoding="utf-8") as f:
            full_text = f.read()
            return full_text
        
def construct_pre_prompt(SR_title, SR_abstract, SR_objective, SR_method):
    prompt = f"""
### Systematic Review: Title, Abstract, Objectives and Methodologies
**Title of Systematic Reivew**:
{SR_title}

**Abstract of Systematic Review**:
{SR_abstract}

**Objective of the Systematic Review**:
{SR_objective}

**Methodology of the Systematic Review**:
{SR_method}

### Instructions
You are conducting a **full-text screening** for a **systematic review and meta-analysis**. Before I provide you with the full-text articles, **identify the key components** of the full text that are essential for determining whether an article should be **included or excluded** in the systematic review.
You may consider the following aspects:
- **Population:** Does the study focus on the specific patient population relevant to this review (e.g., age group, medical condition, gender, or clinical status)?
- **Intervention:** Does the article investigate the medical intervention of interest (e.g., a specific drug, surgical procedure, lifestyle intervention, or medical device)?
- **Comparison:** Does the study compare the intervention to an appropriate control (e.g., placebo, no treatment, standard care, or an alternative treatment)?
- **Outcome:** Are the outcomes measured in the study relevant to the review (e.g., clinical outcomes, mortality rates, disease progression, quality of life)?
- **Study Design:** Is the study design appropriate for answering the research question (e.g., randomized controlled trials, cohort studies, case-control studies)?
"""
    
    pre_prompt = gpt_o3_mini(prompt, "full text pre-prompt")
    print(pre_prompt)
    return pre_prompt


def parse_text_to_JSON(text, component):
    prompt = f"""
### Raw Text
{text}

### Important Components
{component}

### Instructions
1. **Carefully analyze the raw text** and extract the corresponding content for each section.
2. **Ensure accurate mapping** even if section headers are implicit or not well-structured.
3. **If a section is missing, return an empty string ("")** in the JSON response rather than omitting it.

### Output format
The response should always contain `"title"` and `"abstract"`. We will return the extracted content in JSON format. For example:
```json
{{
    "title": "",
    "abstract": "",
    "introduction": "",
    "methods": "",
    "results": "",
    "discussion": "",
    "conclusion": "",
}}
"""
    parsed_text = gpt_4o_mini(prompt, "full text extracter")
    print(parsed_text)
    return parsed_text


def construct_full_text_screening_prompt(SR_title, SR_abstract, SR_objective, SR_method, full_text):
    PICOS_prompt = "### Systematic Review: Title, Abstract\n"
    PICOS_prompt += f"**Title:** {SR_title}\n"
    PICOS_prompt += f"**Abstract:** {SR_abstract}\n"
    
    PICOS_prompt += "### Pre-prompt, including objectives and methodologies\n"
    PICOS_prompt += "Our systematic review is governed by the following objectives and methodologies:\n"

    PICOS_prompt += "**Objectives:**\n"
    PICOS_prompt += f"{SR_objective}\n\n"
    PICOS_prompt += "**Methodologies:**\n"
    PICOS_prompt += f"{SR_method}\n\n"

    PICOS_prompt += "\n### Full-text Article in investigation\n"
    PICOS_prompt += f"{full_text}\n\n"

    PICOS_prompt += "### Instructions, including abstract considerations\n"
    PICOS_prompt += "We now read through and understand the components carefully, and assess whether the article should be included in the systematic review by evaluating the contents from 5 perspectives: Population, Intervention, Control, Outcomes and Study Design (PICOS).\n"
    PICOS_prompt += "Some example criteria for reference, but not limited to:\n"
    PICOS_prompt += "- **Population:** Does the study focus on the specific patient population relevant to this review (e.g., age group, medical condition, gender, or clinical status)?\n"
    PICOS_prompt += "- **Intervention:** Does the article investigate the medical intervention of interest (e.g., a specific drug, surgical procedure, lifestyle intervention, or medical device)?\n"
    PICOS_prompt += "- **Comparison:** Does the study compare the intervention to an appropriate control (e.g., placebo, no treatment, standard care, or an alternative treatment)?\n"
    PICOS_prompt += "- **Outcome:** Are the outcomes measured in the study relevant to the review (e.g., clinical outcomes, mortality rates, disease progression, quality of life)?\n"
    PICOS_prompt += "- **Study Design:** Is the study design appropriate for answering the research question (e.g., randomized controlled trials, cohort studies, case-control studies)?\n\n"
    
    PICOS_prompt += "### Tasks\n"
    PICOS_prompt += "First, always remember to reflect on the contents of both systematic review and article in investigation. Then, we will think step by step for each perspective, giving reasons for why or why not the article in investigation align with our systematic review.\n"
    PICOS_prompt += "\n### Importances\n"
    PICOS_prompt += """
Your primary responsibility in this stage is to ensure that only truly relevant articles are included to minimize false positives.
However, be lenient. studies that may not fully align with the primary focus of our inclusion criteria but provide data or insights potentially relevant to our review deserve thoughtful consideration for inclusion.
"""

    # PICOS_prompt += "Most importantly, our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant.\n"
    
    PICOS_prompt += "\n### Output format\n"
    PICOS_prompt += "We will conclude by outputting (on the very last line) 'XXX' if the article warrants exclusion, or 'YYY' if inclusion is advised or uncertainty persists. We must output either 'XXX' or 'YYY'.\n"

    return PICOS_prompt

def full_text_reviewer(SR_title, SR_abstract, SR_objective, SR_method, CA_full_text, decision, Justification):
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

### Candidate article that is being evaluated for the systematic review: Full Text
{CA_full_text}

### Decision from another medical researcher
Another medical researcher has decided the candidate article to be {decision}, and written the following justification for it.
{Justification}

### Instructions
Your task is to evaluate the justification this medical researcher has given, and decide whether the decision it made is correct or wrong.

### Output format
We will conclude by outputting (on the very last line) 'XXX' if you agree with the medical researcher, or 'YYY' if you disagree with it. We must output either 'XXX' or 'YYY'.
"""
    while True:
        evaluation = gpt_o3_mini(raw_prompt, "detailed screener reviewer")
        print(evaluation)
        if re.search("XXX", evaluation, re.IGNORECASE):
            decision = True
        elif re.search("YYY", evaluation, re.IGNORECASE):
            decision = False
        else:
            continue

        return evaluation, decision

def full_text_improver(SR_title, SR_abstract, SR_objective, SR_method, CA_full_text, feedback):
    raw_prompt = construct_full_text_screening_prompt(SR_title, SR_abstract, SR_objective, SR_method, CA_full_text)
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
    while True:
        improver_resp = gpt_4o_mini(msg_thread)
        print(improver_resp)
        if re.search("XXX", improver_resp, re.IGNORECASE):
            decision = "excluded"
        elif re.search("YYY", improver_resp, re.IGNORECASE):
            decision = "included"
        else:
            continue
        
        return improver_resp, decision


def execute(idx_list):
    for idx in idx_list:
        data_file = open(f"4o-mini_with_reviewer\\gpt2_{idx+1}.txt", "r", encoding="utf-8")
        output_file = open(f"4o-mini_with_reviewer\\gpt3_{idx+1}.txt", "w+", encoding="utf-8")
        
        print(all_titles_LR.titles[idx])

        data = data_file.readlines()

        SR_title = all_titles_LR.titles[idx]
        SR_abstract = all_abstracts_LR.abstracts[idx]
        SR_objective = all_objectives_LR.objectives[idx]
        SR_method = all_methods_LR.methods[idx]

        for line in data:
            if not line.strip():
                continue
            candidate_title = line.split("$$$")[0]
            full_text = retrieve_full_text("reference_15", candidate_title)
            if full_text == "No match found":
                output_file.write(f"{candidate_title}\n")
                continue
            pre_prompt = construct_pre_prompt(SR_title, SR_abstract, SR_objective, SR_method)
            parsed_text = parse_text_to_JSON(full_text, pre_prompt)
            prompt = construct_full_text_screening_prompt(SR_title, SR_abstract, SR_objective, SR_method, parsed_text)

            while True:
                gpt_ans = gpt_4o_mini(prompt, tier="detailed screener")
                print(gpt_ans)
                if re.search("YYY", gpt_ans, re.IGNORECASE):
                    decision = "included"
                elif re.search("XXX", gpt_ans, re.IGNORECASE):
                    decision = "excluded"
                else:
                    continue
                evaluation, agreement = full_text_reviewer(SR_title, SR_abstract, SR_objective, SR_method, parsed_text, decision, gpt_ans)
                if not agreement:
                    _, decision = full_text_improver(SR_title, SR_abstract, SR_objective, SR_method, parsed_text, evaluation)
                if decision == "included":
                    output_file.write(f"{candidate_title}\n")
                break
                        


if __name__ == "__main__":
    idx_list = [14]
    execute(idx_list)
