import requests
from bs4 import BeautifulSoup
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..\\..')))

title = ["Outpatient treatment of confirmed COVID-19: a living, rapid evidence review for the American College of Physicians (version 2)",
    "Effects of dairy intake on markers of cardiometabolic health in adults: a systematic review with network meta-analysis",
    "Systemic pharmacological treatments for chronic plaque psoriasis: a network meta-analysis",
    "Outpatient Treatment of Confirmed COVID-19: A Living, Rapid Review for the American College of Physicians"]

abstract = ["""Background:
Clinicians and patients want to know the benefits and harms of outpatient treatment options for the Omicron variant of SARS-CoV-2.

Purpose:
To assess the benefits and harms of 22 different COVID-19 treatments.

Data Sources:
The Epistemonikos COVID-19 L·OVE platform, the iSearch COVID-19 portfolio, and the World Health Organization (WHO) COVID-19 Research Database from 26 November 2021 to 2 March 2023.

Study Selection:
Two reviewers independently screened abstracts and full texts against a priori–defined criteria.

Data Extraction:
One reviewer extracted the data and assessed the risk of bias and certainty of evidence (COE). A second reviewer verified the data abstraction and assessments.""",

"""
The health effects of dairy products are still a matter of scientific debate owing to inconsistent findings across trials. Therefore, this systematic review and network meta-analysis (NMA) aimed to compare the effects of different dairy products on markers of cardiometabolic health. A systematic search was conducted in 3 electronic databases [MEDLINE, Cochrane Central Register of Controlled Trials (CENTRAL), and Web of Science; search date: 23 September 2022]. This study included randomized controlled trials (RCTs) with a ≥12-wk intervention comparing any 2 of the eligible interventions [e.g., high dairy (≥3 servings/d or equal amount in grams per day), full-fat dairy, low-fat dairy, naturally fermented milk products, and low dairy/control (0-2 servings/d or usual diet)]. A pairwise meta-analysis and NMA using random-effects model was performed in the frequentist framework for 10 outcomes [body weight, BMI, fat mass, waist circumference, low-density lipoprotein cholesterol, high-density lipoprotein (HDL) cholesterol, triglycerides, fasting glucose, glycated hemoglobin, and systolic blood pressure]. Continuous outcome data were pooled using mean differences (MDs) and dairy interventions ranked using the surface under the cumulative ranking curve.

Keywords: body weights and measures; cardiometabolic risk; dairy products; energy intake; glycemic control; network meta-analysis; systematic review.
""",
    
    """
Background: Psoriasis is an immune-mediated disease for which some people have a genetic predisposition. The condition manifests in inflammatory effects on either the skin or joints, or both, and it has a major impact on quality of life. Although there is currently no cure for psoriasis, various treatment strategies allow sustained control of disease signs and symptoms. Several randomised controlled trials (RCTs) have compared the efficacy of the different systemic treatments in psoriasis against placebo. However, the relative benefit of these treatments remains unclear due to the limited number of trials comparing them directly head to head, which is why we chose to conduct a network meta-analysis.

Objectives: To compare the efficacy and safety of conventional systemic agents (acitretin, ciclosporin, fumaric acid esters, methotrexate), small molecules (apremilast, tofacitinib, ponesimod), anti-TNF alpha (etanercept, infliximab, adalimumab, certolizumab), anti-IL12/23 (ustekinumab), anti-IL17 (secukinumab, ixekizumab, brodalumab), anti-IL23 (guselkumab, tildrakizumab), and other biologics (alefacept, itolizumab) for patients with moderate to severe psoriasis and to provide a ranking of these treatments according to their efficacy and safety.

Search methods: We searched the following databases to December 2016: the Cochrane Skin Specialised Register, the Cochrane Central Register of Controlled Trials (CENTRAL), MEDLINE, Embase, and LILACS. We also searched five trials registers and the U.S. Food and Drug Administration (FDA) and European Medicines Agency (EMA) reports. We checked the reference lists of included and excluded studies for further references to relevant RCTs. We searched the trial results databases of a number of pharmaceutical companies and handsearched the conference proceedings of a number of dermatology meetings.

Selection criteria: Randomised controlled trials (RCTs) of systemic and biological treatments in adults (over 18 years of age) with moderate to severe plaque psoriasis or psoriatic arthritis whose skin had been clinically diagnosed with moderate to severe psoriasis, at any stage of treatment, in comparison to placebo or another active agent.

Data collection and analysis: Three groups of two review authors independently undertook study selection, data extraction, 'Risk of bias' assessment, and analyses. We synthesised the data using pair-wise and network meta-analysis (NMA) to compare the treatments of interest and rank them according to their effectiveness (as measured by the Psoriasis Area and Severity Index score (PASI) 90) and acceptability (the inverse of serious adverse effects). We assessed the certainty of the body of evidence from the NMA for the two primary outcomes, according to GRADE; we evaluated evidence as either very low, low, moderate, or high. We contacted study authors when data were unclear or missing.

""",

"""
Background:
Clinicians and patients want to know the benefits and harms of outpatient treatment options for SARS-CoV-2 infection.

Purpose:
To assess the benefits and harms of 12 different COVID-19 treatments in the outpatient setting.

Data Sources:
Epistemonikos COVID-19 L·OVE Platform, searched on 4 April 2022.

Study Selection:
Two reviewers independently screened abstracts and full texts against a priori–defined criteria. Randomized controlled trials (RCTs) that compared COVID-19 treatments in adult outpatients with confirmed SARS-CoV-2 infection were included.

Data Extraction:
One reviewer extracted data and assessed risk of bias and certainty of evidence (COE). A second reviewer verified data abstraction and assessments.
"""

]


objective = ["""
The goal of this rapid review (version 2) was to systematically collate and assess the evidence regarding the benefits and harms of COVID-19 treatments in populations infected with the Omicron variant of SARS-CoV-2. It did not aim to provide treatment guidance but rather to provide evidence to support the American College of Physicians (ACP) Population Health and Medical Science Committee (PHMSC) in updating its practice points on the use of COVID-19 treatments in adult outpatients (8).
""", 
             """
this systematic review with NMA aimed to investigate the comparative effects of dairy intake (e.g., control/low dairy; high dairy; low-fat, high dairy; and full-fat, high dairy) and specific dairy products (e.g., milk, yogurt, kefir, and cheese) on markers of cardiometabolic health in the general healthy adult population.
""",

"""
To compare the efficacy and safety of non‐biological systemic agents (acitretin, ciclosporin, fumaric acid esters, methotrexate), small molecules (apremilast, deucravacitinib), anti‐TNF alpha (etanercept, infliximab, adalimumab, certolizumab), anti‐IL12/23 (ustekinumab), anti‐IL17 (secukinumab, ixekizumab, brodalumab, bimekizumab, sonelokimab, netakimab), and anti‐IL23 (guselkumab, tildrakizumab, risankizumab) for people with moderate‐to‐severe psoriasis using a network meta‐analysis, and to provide a ranking of these treatments according to their efficacy and safety.

A secondary objective is to maintain the currency of the evidence, using a living systematic review approach.
""",

"""
Several reviews have systematically assessed the efficacy and safety of these therapies (3–10). However, given the pace of the pandemic and the emerging evidence, without regular updates these reviews quickly become outdated. In addition, most included both inpatient and outpatient management and focused only on 1 specific COVID-19 treatment. The aim of this living, rapid review was to systematically collate and assess the evidence regarding the benefits and harms of COVID-19 treatments of interest to support the American College of Physicians (ACP) Scientific Medical Policy Committee (SMPC) in developing practice points on the use of COVID-19 treatments in adult outpatients.
"""
]

method = ["""
We addressed the following key questions (KQs):

KQ: What are the benefits and harms of COVID-19 treatments in symptomatic and asymptomatic adult patients with a confirmed SARS-CoV-2 infection in the outpatient setting?

KQa: Do the benefits and harms vary by patient characteristics (age, gender, socioeconomic status, or comorbid conditions), type of SARS-CoV-2 variant, immunity status (prior SARS-CoV-2 infection, vaccination status, or time since infection or vaccination), symptom duration, or disease severity?

We considered randomized controlled trials (RCTs) and prospective and retrospective cohort studies that included adult outpatients with a confirmed diagnosis of acute SARS-CoV-2 infection and that were published in the English language. The enrollment of participants to the study had to start on or after 26 November 2021, when the WHO first described the SARS-CoV-2 Omicron variant (12). Cohort studies had to include more than 5000 participants and had to use any type of statistical analysis that adjusted for age, comorbid conditions, vaccination status, and COVID-19 severity.

The treatments of interest included azithromycin, camostat mesylate, chloroquine–hydroxychloroquine, chlorpheniramine, colchicine, convalescent plasma, corticosteroids, ensitrelvir, favipiravir, fluvoxamine, ivermectin, lopinavir–ritonavir, molnupiravir, neutralizing monoclonal antibodies, metformin, niclosamide, nitazoxanide, nirmatrelvir–ritonavir, and remdesivir. For inclusion in this review, the monoclonal antibodies needed to be approved by the U.S. Food and Drug Administration (FDA) or the European Medicines Agency (EMA) for the treatment of COVID-19 as of the search date. The comparators were placebo or usual care.

During the study selection, we adapted the study protocol to include cohort studies that did not consider COVID-19 severity as a confounding factor and that compared a specific treatment with “no use of the treatment.” This adjustment was necessary because we observed the above pattern in many of the published cohort studies and we would not have been able to include this evidence using our original exclusion criteria, leaving us with very few studies in this review.
""",
          """
Population
We considered studies conducted in the general adult population (age 18 y or older). Studies focusing on children and adolescents, pregnant women, or patients with chronic diseases (e.g., cancer, chronic kidney disease, cardiovascular disease, and type 2 diabetes) were excluded.

Intervention
We considered interventions focusing on the intake/consumption of dairy products (e.g., total dairy, full-fat dairy, low-fat dairy, and naturally fermented milk products). Nonbovine milk and dairy products (e.g., from sheep, goats, buffalos, and camels), milk/protein isolates (e.g., whey or casein), capsules, fortified dairy products (e.g., fortified with vitamin D, plant sterols/stanols, prebiotics, probiotics, or omega-3 fatty acids), and fermented milk products with additional microbiota strains (beyond those naturally occurring) were excluded.

Comparator
We considered the intake of other dairy products, diets low in dairy intake, or usual diets as comparators. Studies were excluded if energy intake differed between the intervention and control arms within a RCT. Co-interventions (e.g., physical activity and calorie restriction) were allowed as long as they were balanced across the study arms within a RCT.

Outcomes
As markers of cardiometabolic health, we considered anthropometric outcomes [body weight (in kilograms), BMI (in kilograms per squared meter), fat mass (in kilograms), and waist circumference (in centimeters)]; blood lipids [low-density lipoprotein (LDL) cholesterol (in millimoles per liter), high-density lipoprotein (HDL) cholesterol (in millimoles per liter), and triglycerides (in millimoles per liter)]; markers of glycemic control [fasting glucose (in millimoles per liter) and glycated hemoglobin (HbA1c; in percentages)]; and systolic blood pressure (millimeters of mercury). In addition, we considered dietary adherence measured by energy intake (in kilocalories per day) and further markers such as consumed dairy servings per day or counting empty packaging.

Study design
We included RCTs with a parallel or crossover design. Crossover trials were considered for NMA only if data from the first intervention period were available to avoid potential carryover effects [20]. Regarding several of the chosen outcomes (e.g., glycated hemoglobin or body weight) [21] and the corresponding time needed for a response to a dietary intervention, we included RCTs of at least 12 wk of intervention.
""",

"""
Types of studies We included randomised controlled trials (RCTs).
Phase I trials were not eligible because participants, outcomes, dosages, and schema of administration of interventions are too different from phase II, III, and IV studies. Cross‐over trials were not eligible (because of the unpredictable evolution of psoriasis and risk of carry‐over bias). Non‐randomised studies, including follow‐up studies, were not eligible.

Types of participants We considered trials that included adults (over 18 years of age) with moderate‐to‐severe plaque psoriasis (i.e. needed systemic treatment) or psoriatic arthritis whose skin had been clinically diagnosed with moderate‐to‐severe psoriasis and who were at any stage of treatment.
Types of interventions
Adaptive criteria for considering studies for this review As a living systematic review, we are continually identifying new evidence for interventions already in the network of trials but also for novel interventions. To provide an update and a useful network of interventions for physicians, we need first to identify new interventions but also, to drop old interventions, which are no longer of interest.

Types of outcome measures Psoriasis is a chronic disease; treatments are symptomatic, often with a return to baseline after discontinuation. The core outcome set for psoriasis clinical trials was defined under the auspices of the International Dermatology Outcome Measures group, whereby the authors conducted a Delphi survey and identified the following 6 domains: (1) skin manifestations of psoriasis (including location), (2) an investigator global assessment, (3) an evaluation of signs and symptoms of both psoriasis and psoriatic arthritis, (4) a patient global assessment of their condition, (5) an assessment of treatment satisfaction, and (6) a measure of health‐related quality of life (Callis Duffin 2018).

""",

"""
KQ: What are the benefits and harms of COVID-19 treatments in symptomatic and asymptomatic adult patients with a confirmed SARS-CoV-2 infection in the outpatient setting?

KQa: Do the benefits and harms vary by patient characteristics (age, gender, or comorbid conditions), type of SARS-CoV-2 variant, immunity status (prior SARS-CoV-2 infection, vaccination status, or time since infection or vaccination), symptom duration, or disease severity?

We considered RCTs that included adult outpatients with a confirmed diagnosis of SARS-CoV-2 infection and were published in English. Treatments of interest included antiviral drugs, neutralizing monoclonal antibodies, antibiotic or antiparasitic drugs, convalescent plasma, corticosteroids, and fluvoxamine. Comparators were placebo to determine treatment efficacy or standard of care if no placebo-controlled trials were available, which was not the case for any of the treatments of interest.

The ACP SMPC selected all-cause mortality, COVID-19–specific mortality, recovery, time to recovery, hospitalization due to COVID-19, and incidences of serious or any adverse events as critical outcomes for decision making. Supplement Table 1 presents the a priori–specified inclusion and exclusion criteria.
"""
]


first_papersIncluded = ["Molnupiravir plus usual care versus usual care alone as early treatment for adults with COVID-19 at increased risk of adverse outcomes (PANORAMIC): an open-label, platform-adaptive randomised controlled trial.",
                        "Effect of higher-dose ivermectin for 6 days vs placebo on time to sustained recovery in outpatients with COVID-19: a randomized clinical trial.",
                        "Accelerating Covid-19 Therapeutic Interventions and Vaccines (ACTIV)-6 Study Group and Investigators.",
                        "Change in effectiveness of sotrovimab for preventing hospitalization and mortality for at-risk COVID-19 outpatients during an Omicron BA.1 and BA.1.1-predominant phase.",
                        "Real-world use of nirmatrelvir-ritonavir in outpatients with COVID-19 during the era of omicron variants including BA.4 and BA.5 in Colorado, USA: a retrospective cohort study.",
                        "Real-world effectiveness of molnupiravir and nirmatrelvir plus ritonavir against mortality, hospitalisation, and in-hospital outcomes among community-dwelling, ambulatory patients with confirmed SARS-CoV-2 infection during the omicron wave in Hong Kong: an observational study.",
                        "Paxlovid associated with decreased hospitalization rate among adults with COVID-19 - United States, April-September 2022.",
                        "Population-based evaluation of the effectiveness of nirmatrelvir-ritonavir for reducing hospital admissions and mortality from COVID-19.",
                        "Nirmatrelvir use and severe Covid-19 outcomes during the Omicron surge."]


second_papersIncluded = ["Effects of regular kefir consumption on gut microbiota in patients with metabolic syndrome: a parallel-group, randomized, controlled study. Nutrients.",
                        "High intake of dairy during energy restriction does not affect energy balance or the intestinal microflora compared with low dairy intake in overweight individuals in a randomized controlled trial.",
                        "Yogurt consumption and estrogen metabolism in healthy premenopausal women.",
                        "Yogurt improves insulin resistance and liver fat in obese women with nonalcoholic fatty liver disease and metabolic syndrome: a randomized controlled trial.",
                        "Effect of high milk and sugar-sweetened and non-caloric soft drink intake on insulin sensitivity after 6 months in overweight and obese adults: a randomized controlled trial.",
                        "Dairy products do not lead to alterations in body weight or fat mass in young women in a 1-y intervention.",
                        "The impact of calcium and dairy product consumption on weight loss.",
                        "High intake of regular-fat cheese compared with reduced-fat cheese does not affect LDL cholesterol or risk markers of the metabolic syndrome: a randomized controlled trial.",
                        "Consumption of low-fat dairy foods for 6 months improves insulin resistance without adversely affecting lipids or bodyweight in healthy adults: a randomized free-living cross-over study.",
                        "The impact of diets rich in low-fat or full-fat dairy on glucose tolerance and its determinants: a randomized controlled trial.",
                        "A randomized intervention trial of 24-wk dairy consumption on waist circumference, blood pressure, and fasting blood sugar and lipids in japanese men with metabolic syndrome.",
                        "Effects of calcium and resistance exercise on body composition in overweight premenopausal women.",
                        "Effect of energy-reduced diets high in dairy products and fiber on weight loss in obese adults.",
                        "Dairy foods in a moderate energy restricted diet do not enhance central fat,weight, and intra-abdominal adipose tissue losses nor reduce adipocyte size or inflammatory markers in overweight and obese adults: a controlled feeding study.",
                        "Dairy products and metabolic effects in overweight men and women: results from a 6-mo intervention study.",
                        "Calcium and dairy acceleration of weight and fat loss during energy restriction in obese adults.",
                        "Effects of calcium and dairy on body composition and weight loss in African-American adults.",
                        "Dairy-rich diets augment fat loss on an energy-restricted diet: a multicenter trial."]

# def get_third():
#     third_papersIncluded = open("Tran_Result_2025/third_papersIncluded.txt", "w+", encoding="utf-8")
#     # URL to scrape
#     url = 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9125768/#CD011535-bbs1-0001title'

#     # Define headers to mimic a real browser
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
#     }

#     # Send a GET request to the website with the headers
#     response = requests.get(url, headers=headers)

#     # Check if the request was successful
#     if response.status_code == 200:
#         # Parse the page content using BeautifulSoup
#         soup = BeautifulSoup(response.content, 'html.parser')

#         # Find all elements with the class 'ref-title' within the structure
#         titles = soup.select('div.ref-list-sec.sec ul.first-line-outdent span.ref-title')

#         # Extract and print the text content of each title
#         for index, subtitle in enumerate(titles):
#             print(f"Title {index+1}: {title.get_text()}")
#             third_papersIncluded.write(subtitle.get_text())
#     else:
#         print(f"Failed to retrieve the page. Status code: {response.status_code}")


def get_third():
    file = open("Tran_Result_2025\\third_papersIncluded.txt", "r")
    content = file.readlines()
    third_papersIncluded = []
    for line in content:
        third_papersIncluded.append(line.strip())
    print(len(third_papersIncluded))
    return third_papersIncluded

third_papersIncluded = get_third()



fourth_papersIncluded = [
    "Early high-titer plasma therapy to prevent severe Covid-19 in older adults",
    "REGEN-COV antibody combination and outcomes in outpatients with Covid-19",
    "Effect of ivermectin on time to resolution of symptoms among adults with mild COVID-19: a randomized clinical trial",
    "Assessing the efficacy and safety of hydroxychloroquine as outpatient treatment of COVID-19: a randomized controlled trial",
    "Randomized double-blinded placebo-controlled trial of hydroxychloroquine with or without azithromycin for virologic cure of non-severe Covid-19",
    "The effect of early treatment with ivermectin on viral load, symptoms and humoral response in patients with non-severe COVID-19: a pilot, double-blind, placebo-controlled, randomized clinical trial",
    "Effect of early treatment with hydroxychloroquine or lopinavir and ritonavir on risk of hospitalization among patients with COVID-19: the TOGETHER randomized clinical trial",
    "A phase 2a clinical trial of molnupiravir in patients with COVID-19 shows accelerated SARS-CoV-2 RNA clearance and elimination of infectious virus",
    "Early use of nitazoxanide in mild COVID-19 disease: randomised, placebo-controlled trial",
    "Molnupiravir for oral treatment of Covid-19 in nonhospitalized patients",
    "Efficacy and safety of regdanvimab (CT-P59): a phase 2/3 randomized, double-blind, placebo-controlled trial in outpatients with mild-to-moderate coronavirus disease 2019",
    "Oral nirmatrelvir for high-risk, nonhospitalized adults with Covid-19",
    "Early convalescent plasma for high-risk outpatients with Covid-19",
    "High-titre methylene blue-treated convalescent plasma as an early treatment for outpatients with COVID-19: a randomised, placebo-controlled trial",
    "Effect of sotrovimab on hospitalization or death among high-risk patients with mild to moderate COVID-19: a randomized clinical trial",
    "Effect of early treatment with fluvoxamine on risk of emergency care and hospitalisation among patients with COVID-19: the TOGETHER randomised, platform clinical trial",
    "Fluvoxamine vs placebo and clinical deterioration in outpatients with symptomatic COVID-19: a randomized clinical trial",
    "Effect of oral azithromycin vs placebo on COVID-19 symptoms in outpatients with SARS-CoV-2 infection: a randomized clinical trial",
    "Safety, virologic efficacy, and pharmacokinetics of CT-P59, a neutralizing monoclonal antibody against SARS-CoV-2 spike receptor-binding protein: two randomized, placebo-controlled, phase I studies in healthy individuals and patients with mild SARS-CoV-2 infection",
    "A randomized double-blind placebo-controlled clinical trial of nitazoxanide for treatment of mild or moderate COVID-19",
    "Early remdesivir to prevent progression to severe Covid-19 in outpatients",
    "Inhaled and intranasal ciclesonide for the treatment of Covid-19 in adult outpatients: CONTAIN phase II randomised controlled trial",
    "Early outpatient treatment for Covid-19 with convalescent plasma",
    "Ivermectin to prevent hospitalizations in patients with COVID-19 (IVERCOR-COVID19) a randomized, double-blind, placebo-controlled trial",
    "High-dose ivermectin for early treatment of COVID-19 (COVER study): a randomised, double-blind, multicentre, phase II, dose-finding, proof-of-concept clinical trial",
    "Effect of early treatment with ivermectin among patients with Covid-19"
]
