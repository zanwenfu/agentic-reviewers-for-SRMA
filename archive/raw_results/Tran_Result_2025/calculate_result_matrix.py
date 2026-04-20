import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dataset.PICOS_data import second_papersIncluded

FP = 0
FN = 0
TP = 0
TN = 0
TOTAL_FILTERED = 0


def check_included_articles_raw(idx: int):

    # directory = "literature_review\\dataset"
    # data_file_paths = [f for f in os.listdir(directory) if f.startswith(str(idx+1)+"_")]
    # print(f"Reference {idx+1}:")

    curr_included_articles = [x.lower() for x in second_papersIncluded]
    # print(len(curr_included_articles))
    size = 0
    total = set()
    for id in [1, 3, 4, 5]:
        data_file = open(f"data\\PICOS\\Kiesswetter{id}.txt", "r", encoding="utf-8")
        data = data_file.readlines()
        size += len(data)
        for line in data:
            if len(line.strip()) == 0:
                break
            curr_title = line.split("$$$")[0].strip().lower()
            if curr_title in curr_included_articles or curr_title+"." in curr_included_articles or curr_title[:-1] in curr_included_articles:
                if curr_title.endswith("."):
                    total.add(curr_title)
                else:
                    total.add(curr_title+".")

    print(size)

    return len(total), size, total


def check_included_articles_filtered(idx: int):
    global TOTAL_FILTERED

    curr_included_articles = [x.lower() for x in second_papersIncluded]
    total_included = set()
    total_filtered = set()

    results = []

    for id in [1, 3, 4, 5]:
        file = open(f"Tran_Result_2025\\Final\\Kiesswetter{id}.txt", "r", encoding="utf-8")
        content = file.readlines()
        results.extend(content)

    for line in results:
        if len(line.strip()) == 0:
            continue
        curr_title = line.split("$$$")[0].strip().lower()
        if curr_title.endswith("."):
            total_filtered.add(curr_title)
        else:
            total_filtered.add(curr_title+".")
        if curr_title in curr_included_articles or curr_title+"." in curr_included_articles or curr_title[:-1] in curr_included_articles:
            if curr_title.endswith("."):
                total_included.add(curr_title)
            else:
                total_included.add(curr_title+".")

    TOTAL_FILTERED = len(total_filtered)

    return len(total_included), total_included


def execute(index_list: list):
    global TP, FN

    for idx in index_list:
        num_included_raw, TOTAL_RAW, total_included = check_included_articles_raw(idx)
        num_included_filtered, total_filtered = check_included_articles_filtered(idx)
        TP = num_included_filtered
        FN = num_included_raw - num_included_filtered
        FP = TOTAL_FILTERED - num_included_filtered
        TN = TOTAL_RAW - TP - FN - FP

        print(total_included - total_filtered)
        
        print(f"FP: {FP}, FN: {FN}, TP: {TP}, TN: {TN}")
        print("FP Rate:", FP/(FP + TN))
        print("FN Rate:", FN/(FN + TP))


execute([1])
