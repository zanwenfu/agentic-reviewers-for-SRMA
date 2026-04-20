import ast
import re
import os
from openai import OpenAI
import time

from literature_review.data import all_titles_LR, all_abstracts_LR, all_objectives_LR, all_methods_LR, all_included_articles_LR


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


def construct_prompt(SR_title, SR_abstract, SR_objective, SR_method, candidate_title, candidate_abstract):
    msg_thread = []

    def add_msg(role, content):
        return msg_thread.append({"role": role, "content": content})

    add_msg("system", "You are assisting in a medical systematic review and are tasked with screening and evaluating the relevance of articles.")

    PICOS_prompt = "{Systematic Review: Title, Abstract and Keywords}\n"
    PICOS_prompt += f"-Title: {SR_title}\n"
    PICOS_prompt += f"-Abstract: {SR_abstract}\n"
    PICOS_prompt += "{Pre-prompt, including objectives and methodologies}\n"
    PICOS_prompt += "Our systematic review is governed by the following objectives and methodologies:\n"
    PICOS_prompt += "# Objectives\n"
    PICOS_prompt += f"{SR_objective}\n\n"
    PICOS_prompt += "# Methodologies\n"
    PICOS_prompt += f"{SR_method}\n\n"

    add_msg("user", PICOS_prompt)

    PICOS_prompt = "{Abstract in investigation}\nI give the title and abstract of the article that is in investigation as input.\n"
    PICOS_prompt += f"-Title: {candidate_title}\n"
    PICOS_prompt += f"-Abstract: {candidate_abstract}\n\n"

    add_msg("user", PICOS_prompt)

    PICOS_prompt = "{Instructions, including abstract considerations}\n# Instructions\n"
    PICOS_prompt += "We now access whether the article should be included in the systematic review by evaluating the contents from 5 perspectives: Population, Intervention, Control, Outcomes and Study Design (PICOS).\n"
    PICOS_prompt += "Some example criteria for reference, but not limited to:\n"
    PICOS_prompt += "# Population: Does the study focus on the specific patient population relevant to this review (e.g., age group, medical condition, gender, or clinical status)?\n"
    PICOS_prompt += "# Intervention: Does the article investigate the medical intervention of interest (e.g., a specific drug, surgical procedure, lifestyle intervention, or medical device)?\n"
    PICOS_prompt += "# Comparison: Does the study compare the intervention to an appropriate control (e.g., placebo, no treatment, standard care, or an alternative treatment)?\n"
    PICOS_prompt += "# Outcome: Are the outcomes measured in the study relevant to the review (e.g., clinical outcomes, mortality rates, disease progression, quality of life)?\n"
    PICOS_prompt += "# Study Design: Is the study design appropriate for answering the research question (e.g., randomized controlled trials, cohort studies, case-control studies)?\n\n"
    
    add_msg("user", PICOS_prompt)

    PICOS_prompt = "# Tasks:\n"
    PICOS_prompt += "First, always remember to reflect on the contents of both systematic review and article in investigation. Then, we will think step by step for each perspective, giving reasons for why or why not the article in investigation align with our systematic review.\n"
    PICOS_prompt += "\n# Importances\n"
    PICOS_prompt += "Be lenient. Studies that may not fully align with the primary focus of our inclusion criteria but provide data or insights potentially relevant to our review deserve thoughtful consideration. Given the nature of abstracts as concise summaries of comprehensive research, some degree of interpretation is necessary.\n"

    add_msg("user", PICOS_prompt)
    # PICOS_prompt += "Most importantly, our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant.\n"
    
    PICOS_prompt = "\n# Output format\n"
    PICOS_prompt += "We will conclude by outputting (on the very last line) 'XXX' if the article warrants exclusion, or 'YYY' if inclusion is advised or uncertainty persists. We must output either 'XXX' or 'YYY'.\n"
    PICOS_prompt += "\n{Modle output}\n"

    add_msg("user", PICOS_prompt)

    while True:
        gpt_ans = try_gpt_4(msg_thread)
        print(gpt_ans)
        if re.search("YYY", gpt_ans, re.IGNORECASE):
            return True
        elif re.search("XXX", gpt_ans, re.IGNORECASE):
            return False
    

def execute():

    for idx in [2, 7, 10, 13, 14]:
        data_file = open(f"data\\gpt_{idx+1}.txt", "r", encoding="utf-8")
        output_file = open(f"data\\gpt2_{idx+1}.txt", "w+", encoding="utf-8")
        
        print(all_titles_LR.titles[idx])

        data = data_file.readlines()
        
        for line in data:
            try:
                curr_title = line.split(";")[0].strip()
                curr_abstract = line.split(";")[1].strip()
            except:
                continue

            success = construct_prompt(all_titles_LR.titles[idx], 
                                       all_abstracts_LR.abstracts[idx], 
                                       all_objectives_LR.objectives[idx],
                                       all_methods_LR.methods[idx],
                                       curr_title, 
                                       curr_abstract)
            if success:
                output_file.write(curr_title+"; "+curr_abstract+"\n")

if __name__ == '__main__':
    execute()
