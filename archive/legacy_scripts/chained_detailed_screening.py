import ast
import re
from llms.chatgpt import try_gpt_4

from literature_review.data import all_titles_LR, all_abstracts_LR, all_objectives_LR, all_methods_LR, all_included_articles_LR

def construct_prompt_detailed_screener(SR_title, SR_abstract, SR_objective, SR_method, candidate_title, candidate_abstract):
    PICOS_prompt = "You are assisting in a medical systematic review and are tasked with screening and evaluating the relevance of articles.\n\n"
    PICOS_prompt += "{Systematic Review: Title, Abstract and Keywords}\n"
    PICOS_prompt += f"-Title: {SR_title}\n"
    PICOS_prompt += f"-Abstract: {SR_abstract}\n"
    # PICOS_prompt += f"-Keywords used for searching candidate articles:\n{keyword}\n\n"
    
    PICOS_prompt += "{Pre-prompt, including objectives and methodologies}\n"
    PICOS_prompt += "Our systematic review is governed by the following objectives and methodologies:\n"
    # objective_index = 1
    # for objective in objective_list:
    #     PICOS_prompt += f"{objective_index}. {objective}\n"
    #     objective_index += 1
    PICOS_prompt += "# Objectives\n"
    PICOS_prompt += f"{SR_objective}\n\n"
    PICOS_prompt += "# Methodologies\n"
    PICOS_prompt += f"{SR_method}\n\n"

    PICOS_prompt += "\n{Abstract in investigation}\nI give the title and abstract of the article that is in investigation as input.\n"
    PICOS_prompt += f"-Title: {candidate_title}\n"
    PICOS_prompt += f"-Abstract: {candidate_abstract}\n\n"

    PICOS_prompt += "{Instructions, including abstract considerations}\n# Instructions\n"
    PICOS_prompt += "We now access whether the article should be included in the systematic review by evaluating the contents from 5 perspectives: Population, Intervention, Control, Outcomes and Study Design (PICOS).\n"
    PICOS_prompt += "Some example criteria for reference, but not limited to:\n"
    PICOS_prompt += "# Population: Does the study focus on the specific patient population relevant to this review (e.g., age group, medical condition, gender, or clinical status)?\n"
    PICOS_prompt += "# Intervention: Does the article investigate the medical intervention of interest (e.g., a specific drug, surgical procedure, lifestyle intervention, or medical device)?\n"
    PICOS_prompt += "# Comparison: Does the study compare the intervention to an appropriate control (e.g., placebo, no treatment, standard care, or an alternative treatment)?\n"
    PICOS_prompt += "# Outcome: Are the outcomes measured in the study relevant to the review (e.g., clinical outcomes, mortality rates, disease progression, quality of life)?\n"
    PICOS_prompt += "# Study Design: Is the study design appropriate for answering the research question (e.g., randomized controlled trials, cohort studies, case-control studies)?\n\n"
    
    PICOS_prompt += "# Tasks:\n"
    PICOS_prompt += "First, always remember to reflect on the contents of both systematic review and article in investigation. Then, we will think step by step for each perspective, giving reasons for why or why not the article in investigation align with our systematic review.\n"
    PICOS_prompt += "\n# Importances\n"
    PICOS_prompt += "Be lenient. Studies that may not fully align with the primary focus of our inclusion criteria but provide data or insights potentially relevant to our review deserve thoughtful consideration. Given the nature of abstracts as concise summaries of comprehensive research, some degree of interpretation is necessary.\n"

    # PICOS_prompt += "Most importantly, our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant.\n"
    
    PICOS_prompt += "\n# Output format\n"
    PICOS_prompt += "We will conclude by outputting (on the very last line) 'XXX' if the article warrants exclusion, or 'YYY' if inclusion is advised or uncertainty persists. We must output either 'XXX' or 'YYY'.\n"
    PICOS_prompt += "\n{Modle output}\n"


    gpt_ans = try_gpt_4(PICOS_prompt)
    print(gpt_ans)
    if re.search("YYY", gpt_ans, re.IGNORECASE):
        decision = "included"
    elif re.search("XXX", gpt_ans, re.IGNORECASE):
        decision = "excluded"
    return gpt_ans, decision
    
def reviewer(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract, decision, Justification):
    raw_prompt = f"""
You are an experienced medical researcher conducting a systematic review on the following topic.

### {{Title of Systematic Reivew}}
{SR_title}

### {{Abstract of Systematic Review}}
{SR_abstract}

### {{Objective of the Systematic Review}}
{SR_objective}

### {{Methodology of the Systematic Review}}
{SR_method}

Now a candidate article is being evaluated for the systematic review.

### {{Title of the candidate article}}
{CA_title}

### {{Abstract of the candidate article}}
{CA_abstract}

Another medical researcher has decided the candidate article to be {decision}, and written the following justification for it.
{Justification}

Your task is to evaluate the justification this medical researcher has given, and decide whether the decision it made is correct or wrong.
We will conclude by outputting (on the very last line) 'XXX' if you agree with the medical researcher, or 'YYY' if you disagree with it. We must output either 'XXX' or 'YYY'.
"""
    evaluation = try_gpt_4(raw_prompt)
    print(evaluation)
    if re.search("XXX", evaluation, re.IGNORECASE):
        decision = True
    elif re.search("YYY", evaluation, re.IGNORECASE):
        decision = False

    return evaluation, decision

def improver(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract, feedback):
    raw_prompt = construct_prompt_detailed_screener(SR_title, SR_abstract, SR_objective, SR_method, CA_title, CA_abstract)
    msg_thread = []
    msg_thread.append({"role": "user", "content": raw_prompt})
    msg_thread.append({"role": "user", "content": feedback})
    msg_thread.append({"role": "user", "content": """
Another experienced medical researcher has decided that your justification for the candidate article is incorrect.
Re-evaluate the relevance of the candidate article based on the feedback.
We will conclude by outputting (on the very last line) 'XXX' if the article warrants exclusion, or 'YYY' if inclusion is advised or uncertainty persists. We must output either 'XXX' or 'YYY'.
"""})
    improver_resp = try_gpt_4(msg_thread)
    print(improver_resp)
    if re.search("XXX", improver_resp, re.IGNORECASE):
        decision = "excluded"
    elif re.search("YYY", improver_resp, re.IGNORECASE):
        decision = "included"
    
    return improver_resp, decision


def execute():

    for idx in [2, 7, 13, 14]:
        data_file = open(f"data\\gpt_{idx+1}.txt", "r", encoding="utf-8")
        output_file = open(f"data\\gpt2_{idx+1}.txt", "w+", encoding="utf-8")
        
        print(all_titles_LR.titles[idx])

        data = data_file.readlines()

        SR_title = all_titles_LR.titles[idx]
        SR_abstract = all_abstracts_LR.abstracts[idx]
        SR_objective = all_objectives_LR.objectives[idx]
        SR_method = all_methods_LR.methods[idx]
        total_disagreements = 0
        
        for line in data:
            try:
                curr_title = line.split(";")[0].strip()
                curr_abstract = line.split(";")[1].strip()
            except:
                continue

            success = False
            detailed_screener_resp, decision = construct_prompt_detailed_screener(SR_title, SR_abstract, SR_objective, SR_method, curr_title, curr_abstract)
            while not success:
                reviewer_resp, success = reviewer(SR_title, SR_abstract, SR_objective, SR_method, curr_title, curr_abstract, decision, detailed_screener_resp)
                if not success:
                    total_disagreements += 1
                    detailed_screener_resp, decision = improver(SR_title, SR_abstract, SR_objective, SR_method, curr_title, curr_abstract, reviewer_resp)

            if decision == "included":
                output_file.write(curr_title+"; "+curr_abstract+"\n")

        print(f"Total disagreements: {total_disagreements}")
        output_file.write(f"Total disagreements: {total_disagreements}\n")


if __name__ == '__main__':
    execute()
