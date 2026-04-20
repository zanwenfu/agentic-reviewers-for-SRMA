import ast
import re
import os
from llms.chatgpt import try_gpt_4
from literature_review.data import all_titles_LR, all_abstracts_LR

def construct_prompt_classifier(SR_title, SR_abstract, candidate_title, candidate_abstract):
    ask_chatgpt = f"You are assisting in a medical systematic review and are tasked with screening and categorizing articles based on their relevance.\n"
    ask_chatgpt += "{Systematic Review: Title, Abstract and Keywords}\n"
    ask_chatgpt += f"-Title: \n{SR_title}\n"
    ask_chatgpt += f"-Abstract: \n{SR_abstract}\n"

    ask_chatgpt += "{Abstract in investigation}\n"
    ask_chatgpt += f"I give the title and abstract of the article that is in investigation as input.\n"
    ask_chatgpt += f"-Title: {candidate_title}\n"
    ask_chatgpt += f"-Abstract: {candidate_abstract}\n\n"

    ask_chatgpt += "{Instructions, including abstract considerations}\n# Instructions\n"
    ask_chatgpt += "We now evaluate the relevance of provided article, and categorize it into one of the broad categories: potentially relevant, likely irrelevant, and uncertain.\n"
    ask_chatgpt += "First, we will reflect on the contents of both systematic review and article in investigation. Then we will think step by step, giving reasons for why the articles are categorized as potentially relevant, likely irrelevant, or uncertain.\n"

    ask_chatgpt += "\n# Importance\n"
    ask_chatgpt += "Be lenient. Our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant.\n"
    ask_chatgpt += "# Output format\n"
    ask_chatgpt += "We will conclude by outputting (on the very last line) 'XXX', if the study is potentially relevant. 'YYY', if the study is uncertain. 'ZZZ', if the study is likely irrelevant.\n"

    return ask_chatgpt

def classifier(SR_title, SR_abstract, candidate_title, candidate_abstract):
    ask_chatgpt = construct_prompt_classifier(SR_title, SR_abstract, candidate_title, candidate_abstract)

    justification = try_gpt_4(ask_chatgpt)
    print(justification)
    if re.search("XXX", justification, re.IGNORECASE):
        decision = "potentially relevant"
    elif re.search("YYY", justification, re.IGNORECASE):
        decision = "uncertain"
    elif re.search("ZZZ", justification, re.IGNORECASE):
        decision = "likely irrelevant"

    return justification, decision


def reviewer(SR_title, SR_abstract, CA_title, CA_abstract, decision, Justification):
    raw_prompt = f"""
You are an experienced medical researcher conducting a systematic review on the following topic.

### {{Title of Systematic Reivew}}
{SR_title}

### {{Abstract of Systematic Review}}
{SR_abstract}

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

def improver(SR_title, SR_abstract, CA_title, CA_abstract, feedback):
    raw_prompt = construct_prompt_classifier(SR_title, SR_abstract, CA_title, CA_abstract)
    msg_thread = []
    msg_thread.append({"role": "user", "content": raw_prompt})
    msg_thread.append({"role": "user", "content": feedback})
    msg_thread.append({"role": "user", "content": """
Another experienced medical researcher has decided that your justification for the candidate article is incorrect.
Re-evaluate the relevance of the candidate article based on the feedback.
We will conclude by outputting (on the very last line) 'XXX', if the study is potentially relevant. 'YYY', if the study is uncertain. 'ZZZ', if the study is likely irrelevant.
"""})
    improver_resp = try_gpt_4(msg_thread)
    print(improver_resp)
    if re.search("XXX", improver_resp, re.IGNORECASE):
        decision = "potentially relevant"
    elif re.search("YYY", improver_resp, re.IGNORECASE):
        decision = "uncertain"
    elif re.search("ZZZ", improver_resp, re.IGNORECASE):
        decision = "likely irrelevant"
    
    return improver_resp, decision

def execute():
    directory = "literature_review\\dataset"

    for idx in [2, 7, 13, 14]:
        data_file_paths = [f for f in os.listdir(directory) if f.startswith(str(idx+1)+"_")]
        print(data_file_paths)
        output_file = open(f"data\\gpt_{idx+1}.txt", "w+", encoding="utf-8")
        
        print(all_titles_LR.titles[idx])
        SR_title = all_titles_LR.titles[idx]
        SR_abstract = all_abstracts_LR.abstracts[idx]
        total_disagreements = 0

        for path in data_file_paths:
            data_file = open(f"{directory}\\{path}", "r", encoding="utf-8")
            data = data_file.readlines()
                        
            for line in data:
                curr_title = line.split(";")[0].strip()
                curr_abstract = line.split(";")[1].strip()

                success = False
                classifier_resp, decision = classifier(SR_title, SR_abstract, curr_title, curr_abstract)
                while not success:
                    reviewer_resp, success = reviewer(SR_title, SR_abstract, curr_title, curr_abstract, decision, classifier_resp)
                    if not success:
                        total_disagreements += 1
                        classifier_resp, decision = improver(SR_title, SR_abstract, curr_title, curr_abstract, reviewer_resp)

                if decision in ["potentially relevant", "uncertain"]:
                    output_file.write(curr_title+"; "+curr_abstract+"\n")

        print(f"Total disagreements: {total_disagreements}")
        output_file.write(f"Total disagreements: {total_disagreements}\n")


if __name__ == '__main__':
    execute()
