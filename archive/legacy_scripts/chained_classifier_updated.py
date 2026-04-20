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


def construct_prompt(SR_title, SR_abstract, candidate_title, candidate_abstract):

    msg_thread = []

    msg_thread.append({"role": "system", "content": "You are assisting in a medical systematic review and are tasked with screening and categorizing articles based on their relevance."})
    
    ask_chatgpt = "{Systematic Review: Title, Abstract and Keywords}\n"
    ask_chatgpt += f"-Title: \n{SR_title}\n"
    ask_chatgpt += f"-Abstract: \n{SR_abstract}\n"
    msg_thread.append({"role": "user", "content": ask_chatgpt})

    ask_chatgpt = "{Abstract in investigation}\n"
    ask_chatgpt += f"I give the title and abstract of the article that is in investigation as input.\n"
    ask_chatgpt += f"-Title: {candidate_title}\n"
    ask_chatgpt += f"-Abstract: {candidate_abstract}\n\n"
    msg_thread.append({"role": "user", "content": ask_chatgpt})

    ask_chatgpt = "{Instructions, including abstract considerations}\n# Instructions\n"
    ask_chatgpt += "We now evaluate the relevance of provided article, and categorize it into one of the broad categories: potentially relevant, likely irrelevant, and uncertain.\n"
    ask_chatgpt += "First, we will reflect on the contents of both systematic review and article in investigation. Then we will think step by step, giving reasons for why the articles are categorized as potentially relevant, likely irrelevant, or uncertain.\n"

    ask_chatgpt += "\n# Importance\n"
    ask_chatgpt += "Be lenient. Our aim should be to inclusively screen abstracts, ensuring broad coverage of pertinent studies while filtering out those that are clearly irrelevant.\n"
    ask_chatgpt += "# Output format\n"
    ask_chatgpt += "We will conclude by outputting (on the very last line) 'XXX', if the study is potentially relevant. 'YYY', if the study is uncertain. 'ZZZ', if the study is likely irrelevant.\n"
    msg_thread.append({"role": "user", "content": ask_chatgpt})

    gpt_ans = try_gpt_4(msg_thread)
    print(gpt_ans)
    if re.search("XXX", gpt_ans, re.IGNORECASE) or re.search("YYY", gpt_ans, re.IGNORECASE):
        return True
    else:
        return False
    

def execute():
    directory = "literature_review\\dataset"

    for idx in [2, 7, 10, 13, 14]:
        data_file_paths = [f for f in os.listdir(directory) if f.startswith(str(idx+1)+"_")]
        print(data_file_paths)
        output_file = open(f"data\\gpt_{idx+1}.txt", "w+", encoding="utf-8")
        
        print(all_titles_LR.titles[idx])

        for path in data_file_paths:
            data_file = open(f"{directory}\\{path}", "r", encoding="utf-8")
            data = data_file.readlines()
                        
            for line in data:
                curr_title = line.split(";")[0].strip()
                curr_abstract = line.split(";")[1].strip()

                success = construct_prompt(all_titles_LR.titles[idx], all_abstracts_LR.abstracts[idx], curr_title, curr_abstract)
                if success:
                    output_file.write(curr_title+"; "+curr_abstract+"\n")


if __name__ == '__main__':
    execute()
