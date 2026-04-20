from search import search_article_by_title, fetch_full_text_url, get_full_text_from_url
import targetData
import os
import llms.chatgpt as chatgpt
import ast
import re
import nltk
from nltk.tokenize import word_tokenize
import tiktoken


def get_titles_from_initial_screening(index):
    meta_title = targetData.getTitles()[index]
    initial_screening_file = open(f"data\gpt2_{meta_title}.txt", "r", encoding="utf-8")
    titles = initial_screening_file.readlines()
    
    for title in titles:
        title = title.split(";")
        if len(title) <= 1:
            print("This line is empty. Continue...")
            continue
        title = title[0].strip()
        print(f"Current title is: {title}")
        
        while True:
            try:
                f = open(os.path.join("data", "fulltext", f"fulltext_{title}.txt"), "w+", encoding="utf-8")
                break
            except:
                title = title[:-1]

        f.write(title+"; ")
        try:
            pmid = search_article_by_title(title)
        except:
            f.write("Search article by title got error!\n")
            print(f"Full text URL not found for {title}.")
            continue

        if pmid:
            try:
                full_text_url = fetch_full_text_url(pmid)
                if full_text_url:
                    print(f"Full text URL: {full_text_url}")
                    full_text = get_full_text_from_url(full_text_url)
                    if full_text is None:
                        f.write("No full text found!\n")
                        print(f"Full text URL not found for {title}.")
                    else:
                        f.write(full_text+"\n")
                        print("Wrote full text to file.")
                else:
                    print(f"Full text URL not found for {title}.")
                    f.write("Full text URL not found!\n")
            except:
                f.write("Fetch full text url error!\n")
        else:
            print(f"No article PMID found for {title}!")
            f.write("No article PMID found!\n")

def get_fulltext_url(index):
    meta_title = targetData.getTitles()[index]
    initial_screening_file = open(f"data\gpt2_{meta_title}.txt", "r", encoding="utf-8")
    titles = initial_screening_file.readlines()[2611:]

    f = open(f"data\\fulltext_url_{meta_title}.txt", "a", encoding="utf-8")

    for title in titles:
        title = title.split(";")
        if len(title) != 2:
            print("This line is empty. Continue...")
            continue
        title = title[0].strip()
        print(f"Current title is: {title}")
        f.write(title+"; ")

        try:
            pmid = search_article_by_title(title)
        except:
            f.write("Search article by title got error!\n")
            print(f"Full text URL not found for {title}.")
            continue

        if pmid:
            try:
                full_text_url = fetch_full_text_url(pmid)
                f.write(full_text_url+"\n")
                print(f"Full text URL: {full_text_url}")
            except:
                f.write("Fetch full text url error!\n")
                print("Fetch full text url error!")
              
        else:
            print(f"No article PMID found for {title}!")
            f.write("No article PMID found!\n")

def include_target_articles(query, target_articles):
    result = []
    for paper in query:
        if paper.lower() in target_articles:
            result.append(paper)
    return result

def process_prompt(citation_list, index_value, curr_index_title, curr_fulltext):
    PICOS_prompt = "Objective: I’m performing a systematic review. I am reading FULL TEXT of studies to assess whether or not they should be included in my review. "
    include_citation_list = citation_list[0]
    exclude_citation_list = citation_list[1]

    PICOS_index_dict = {"Population": 0, "Intervention": 1, "Control": 2, "Outcome": 3, "Design": 4}
    PICOS_prompt_dict = {"Population": "population", "Intervention": "treatment", "Control": "control", "Outcome": "outcomes", "Design": "study design"}

    PICOS_prompt += f"On-hand Information: I have study title: {curr_index_title}, and its full text: {curr_fulltext}.\n"
    PICOS_prompt += f"Your Task: Read full text article of the study. Assess the study {PICOS_prompt_dict.get(index_value)} (inclusion and exclusion criterion) and answer using the following algorithm:\n"
    PICOS_index = PICOS_index_dict.get(index_value)
    include_criteria = include_citation_list[PICOS_index]
    exclude_criteria = exclude_citation_list[PICOS_index]
    
    if len(include_criteria) != 0:
        for include in include_criteria:
            PICOS_prompt += f"If the study satisfies: {include},  your answer should contain the word\"INCLUDE\" (in capital letters).\n"
    if len(exclude_criteria) != 0:
        for exclude in exclude_criteria:
            PICOS_prompt += f"If the study satisfies: {exclude},  your answer should contain the word\"EXCLUDE\" (in capital letters).\n"
    PICOS_prompt += "If unclear, your answer should contain the word \"UNKNOWN\" (in capital letters).\n"
    PICOS_prompt += "Your answer: \"INCLUDE\", if the study satisfies \"INCLUDE\" criterion. \"EXCLUDE\", if the study satisfies \"EXCLUDE\" criterion. \"UNKNOWN\", if the study details are unclear. \"ERROR\", if full text article is not accessible.\n\n"

    PICOS_prompt += "Let's think step by step, and provide me with your final answer (Do NOT mention the three answer keywords during your thinking process UNTIL you have the final result): "

    return PICOS_prompt

if __name__ == '__main__':
    title = targetData.getTitles()
    keyword = targetData.getKeywords()
    papersIncluded = targetData.getPapersIncluded()

    i = 0

    while i < len(title):
        # get_fulltext_url(i)
        print(f"Retrieved full text url from all titles for {title[i]}.")

        while True:
            ask_gpt = "I'm applying PICOS (Population, Intervention, Control, Outcomes and Study design) framework to perform FULL TEXT screening of articles.\n"
            ask_gpt += f"For each element of PICOS framework, I need \"INCLUDE\" criterion to decide whether a given article should be included in my systematic review of: {title[i]}.\n"
            ask_gpt += f"Now based on citations (title and abstract) of the meta analysis, provide me with multiple highly relevant \"INCLUDE\" criterion in short sentences."
            ask_gpt += "For each element, you should put your criterion in a python list. In the end, ONLY give me FIVE python lists in the order of FIVE Elements: Population, Intervention, Control, Outcomes and Study design."
            ask_gpt += "I only want list objects, so DO NOT give me any other text and symbols!"

            include_gpt_citations = chatgpt.try_gpt_4(ask_gpt)
            include_citation_list = []

            for citation in iter(include_gpt_citations.splitlines()):
                try:
                    include_citation_list.append(ast.literal_eval(citation.strip()))
                    print("Get include citation!")
                except:
                    print("Include error!")
                    continue

            print("Include citation_list:", len(include_citation_list))

            if len(include_citation_list) == 5:
                break

        while True:
            ask_gpt = "I'm applying PICOS (Population, Intervention, Control, Outcomes and Study design) framework to perform FULL TEXT screening of articles.\n"
            ask_gpt += f"For each element of PICOS framework, I need \"EXCLUDE\" criterion to decide whether a given article should be excluded in my systematic review of: {title[i]}.\n"
            ask_gpt += f"Now based on citations (title and abstract) of the meta analysis, provide me with multiple highly relevant \"EXCLUDE\" criterion in short sentences."
            ask_gpt += "For each element, you should put your criterion in a python list. In the end, ONLY give me FIVE python lists in the order of FIVE Elements: Population, Intervention, Control, Outcomes and Study design."
            ask_gpt += "I only want list objects, so DO NOT give me any other text and symbols!"

            exclude_gpt_citations = chatgpt.try_gpt_4(ask_gpt)
            exclude_citation_list = []

            for citation in iter(exclude_gpt_citations.splitlines()):
                try:
                    exclude_citation_list.append(ast.literal_eval(citation.strip()))
                    print("Get exclude citation!")
                except:
                    print("Exclude error!")
                    continue

            print("Exclude citation_list:", len(exclude_citation_list))

            if len(exclude_citation_list) == 5:
                break

        citation_list = [include_citation_list, exclude_citation_list]
        print(citation_list)

        fulltext_urls = open(f"data\\fulltext_url_{title[i]}.txt", "r", encoding="utf-8")

        article_dict = fulltext_urls.readlines()[0:10]

        num_of_total_articles = len(article_dict)

        f = open(f"data\gpt_fulltext_{title[i]}.txt", "w+", encoding="utf-8")
        f_check = open(f"data\gpt_fulltext_CHECK_{title[i]}.txt", "w+", encoding="utf-8")
        f_no_url = open(f"data\gpt_no_fulltext_{title[i]}.txt", "w+", encoding="utf-8")

        print("length of articles get:", num_of_total_articles)
        f.write(f"Total number of articles searched: {num_of_total_articles}\n")

        f.write(f"Include criteria: {include_citation_list}\n")
        f.write(f"Exclude criteria: {exclude_citation_list}\n")

        print("ready for Chatgpt")
        curr_paper_included = papersIncluded[i]
        curr_target_paper_searched = set()
        curr_target_paper_filtered = set()

        curr_total_articles = set()

        num_of_articles_after_filtered = 0
        
        j = 0
        while j < num_of_total_articles:
            
            if j + 12 < num_of_total_articles:
                    filtered_articles = article_dict[j:j+12]
            else:
                    filtered_articles = article_dict[j:]
            
            new_filtered_articles = []

            for article in filtered_articles:
                try:
                    curr_article = article.split(";")
                    new_filtered_articles.append([curr_article[0].strip(), curr_article[1].strip()])
                except:
                    print("Did not get new filtered articles!")

            filtered_titles = [item[0] for item in new_filtered_articles]

            searched_included_articles = include_target_articles(filtered_titles, curr_paper_included)

            if len(searched_included_articles) != 0:
                for p in searched_included_articles:
                    curr_target_paper_searched.add(p)
                    print("YES PAPERS ARE INCLUDED!")
            # else:
            #     print("No papers included!")
            #     # f.write(str(filtered_titles))
            #     j += 12
            #     continue

            filtered_url = [item[1] for item in new_filtered_articles]

            for curr_index in range(0, len(filtered_titles)):

                curr_index_title = filtered_titles[curr_index]
                curr_index_url = filtered_url[curr_index]

                print(curr_index_url, curr_index_url[:5])

                if curr_index_url[:5] != "https":
                    f_no_url.write(str(curr_index_title)+"; "+ "URL not begin with https!"+"\n")
                    print(f"No URL found for {curr_index_title}")
                    continue

                try:
                    curr_fulltext = get_full_text_from_url(curr_index_url)
                except Exception as e:
                    print(e)
                    f_no_url.write(str(curr_index_title)+"; "+ "get_full_text_from_url got error!"+"\n")
                    print(f"{curr_index_title} get full text from url ERROR!")
                    continue
                
                if curr_fulltext is None:
                    f_no_url.write(str(curr_index_title)+"; "+ "failed to solve captcha!"+"\n")
                    print(f"{curr_index_title} failed to solve captcha!")
                    continue

                # Shorten length of article if it exceed maximum token limit for gpt.
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                # Encode the text to get the tokens
                tokens = encoding.encode(curr_fulltext)
                while len(tokens) > 14000:
                    curr_fulltext = curr_fulltext[0:len(curr_fulltext) - 500]
                    tokens = encoding.encode(curr_fulltext)

                num_of_exclude = 0
                num_of_unknown = 0
                has_URL_error = False

                for element in ["Population", "Design", "Intervention", "Control", "Outcome"]:
                    
                    ask_chatgpt = process_prompt(citation_list, element, curr_index_title, curr_fulltext)
                    gpt_ans = chatgpt.try_gpt_4(ask_chatgpt)

                    try:
                        if re.search("EXCLUDE", gpt_ans, re.IGNORECASE):
                            num_of_exclude += 1
                        if re.search("UNKNOWN", gpt_ans, re.IGNORECASE):
                            num_of_unknown += 1
                        if re.search("ERROR", gpt_ans, re.IGNORECASE):
                            print(gpt_ans)
                            f_no_url.write(str(curr_index_title)+"; "+ "Gpt answer returns ERROR!"+"\n")
                            has_URL_error = True
                            print(f"{curr_index_title} Gpt answer returns ERROR!")
                            break
                    except:
                        print("Error occur when counting EXCLUDE and UNKNOWN!")
                        
                # No Full Text Found.
                if has_URL_error:
                    continue
                
                if num_of_exclude <= 2 and num_of_unknown <= 1:
                    print("Included!")
                    if curr_index_title not in curr_total_articles:
                        f.write(str(curr_index_title)+"; "+str(curr_index_url)+"\n")
                        num_of_articles_after_filtered += 1
                        curr_total_articles.add(curr_index_title)

                        if curr_index_title.lower() in curr_paper_included:
                            curr_target_paper_filtered.add(curr_index_title)
                    
                    else:
                        print(f"{curr_index_title} is already included.")
                        continue
                        
                else:
                    print(f"{curr_index_title} is NOT included!")
                    if curr_index_title.lower() in curr_paper_included:
                        f_check.write(f"{curr_index_title}: Exclude: {num_of_exclude}, Unknown: {num_of_unknown}.\n")

            print(j)
            j += 12

        print(f"Gpt finished {title[i]}")

        f.write(f"\nThere are {len(curr_target_paper_searched)} Target Papers Found during the search in PubMed!\n")
        f.write(f"They are:\n")
        for paper in curr_target_paper_searched:
            f.write(f"{str(paper)}\n")
        f.write(f"\nIn the end, {len(curr_target_paper_filtered)} Target Papers were left after filtering!\n")
        f.write(f"They are:\n")
        for paper in curr_target_paper_filtered:
            f.write(f"{str(paper)}\n")

        diff = len(curr_target_paper_searched) - len(curr_target_paper_filtered)
        f.write(f"\nThe number of target article missing is: {diff}\n")

        FP = num_of_articles_after_filtered / num_of_total_articles
        f.write(f"False Positive Rate: {FP}\n")
        if len(curr_target_paper_searched) != 0:
            FN = diff / len(curr_target_paper_searched)
        else:
            FN = 0
        f.write(f"False Negative Rate: {FN}\n")

        print("Finish writing")

        i += 1
        break




