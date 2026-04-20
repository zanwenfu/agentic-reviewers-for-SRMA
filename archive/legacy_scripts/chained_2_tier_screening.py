import ast
import re
import os
from llms.chatgpt import gpt_o3_mini
from literature_review.data import all_titles_LR, all_abstracts_LR, all_objectives_LR, all_methods_LR, all_included_articles_LR

def construct_prompt_classifier(SR_title, SR_abstract, candidate_title, candidate_abstract):
    ask_chatgpt = f"\n"
    ask_chatgpt += "### Systematic Review: Title, Abstract and Keywords\n"
    ask_chatgpt += f"**Title:** \n{SR_title}\n"
    ask_chatgpt += f"**Abstract:** \n{SR_abstract}\n"

    ask_chatgpt += "### Abstract in investigation\n"
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
    ask_chatgpt = construct_prompt_classifier(SR_title, SR_abstract, candidate_title, candidate_abstract)

    justification = gpt_o3_mini(ask_chatgpt)
    print(justification)
    if re.search("XXX", justification, re.IGNORECASE):
        decision = "potentially relevant"
    elif re.search("YYY", justification, re.IGNORECASE):
        decision = "uncertain"
    elif re.search("ZZZ", justification, re.IGNORECASE):
        decision = "likely irrelevant"

    return justification, decision

def classifier_execute(idx_list):
    directory = "literature_review\\dataset"

    for idx in idx_list:
        data_file_paths = [f for f in os.listdir(directory) if f.startswith(str(idx+1)+"_")]
        print(data_file_paths)
        output_file = open(f"data\\gpt_{idx+1}.txt", "w+", encoding="utf-8")
        
        print(all_titles_LR.titles[idx])
        SR_title = all_titles_LR.titles[idx]
        SR_abstract = all_abstracts_LR.abstracts[idx]

        for path in data_file_paths:
            data_file = open(f"{directory}\\{path}", "r", encoding="utf-8")
            data = data_file.readlines()
                        
            for line in data:
                curr_title = line.split("$$$")[0].strip()
                curr_abstract = line.split("$$$")[1].strip()

                classifier_resp, decision = classifier(SR_title, SR_abstract, curr_title, curr_abstract)

                if decision in ["potentially relevant", "uncertain"]:
                    output_file.write(curr_title+"$$$ "+curr_abstract+"\n")


def construct_prompt_detailed_screening(SR_title, SR_abstract, SR_objective, SR_method, candidate_title, candidate_abstract):
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

    while True:
        gpt_ans = gpt_o3_mini(PICOS_prompt)
        print(gpt_ans)
        if re.search("YYY", gpt_ans, re.IGNORECASE):
            return True
        elif re.search("XXX", gpt_ans, re.IGNORECASE):
            return False
    

def detailed_screening_execute(idx_list):
    for idx in idx_list:
        data_file = open(f"data\\gpt_{idx+1}.txt", "r", encoding="utf-8")
        output_file = open(f"data\\gpt2_{idx+1}.txt", "w+", encoding="utf-8")
        
        print(all_titles_LR.titles[idx])

        data = data_file.readlines()
        
        for line in data:
            try:
                curr_title = line.split("$$$")[0].strip()
                curr_abstract = line.split("$$$")[1].strip()
            except:
                continue

            success = construct_prompt_detailed_screening(all_titles_LR.titles[idx], 
                                       all_abstracts_LR.abstracts[idx], 
                                       all_objectives_LR.objectives[idx],
                                       all_methods_LR.methods[idx],
                                       curr_title, 
                                       curr_abstract)
            if success:
                output_file.write(curr_title+"$$$ "+curr_abstract+"\n")


def execute():
    idx_list = [14]
    classifier_execute(idx_list)
    detailed_screening_execute(idx_list)


if __name__ == '__main__':
    execute()
