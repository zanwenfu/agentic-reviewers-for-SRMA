import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def try_gpt_4(message):
    # NOTE: this file is preserved under archive/ for provenance only.
    # The original hard-coded key was revoked and redacted before open-sourcing.
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    while True:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={ "type": "text" },
                messages=[
                    {"role": "user", "content": message}
                    ],
                    timeout = 20
                    )
            # print(response.choices[0].message.content)
            return response.choices[0].message.content
        except:
            time.sleep(10)
            print("The request timed out.")


def calculate_title_similarity(title1, title2):
    """
    Computes the similarity between two titles using multiple methods.
    Returns a similarity score (0 to 100).
    """
    # Fuzzy string matching (Levenshtein Distance & Token Sort Ratio)
    fuzz_ratio = fuzz.ratio(title1.lower(), title2.lower())  # Basic character-level similarity
    token_sort_ratio = fuzz.token_sort_ratio(title1.lower(), title2.lower())  # Handles word order differences
    
    # TF-IDF Cosine Similarity
    vectorizer = TfidfVectorizer().fit_transform([title1, title2])
    tfidf_sim = cosine_similarity(vectorizer[0], vectorizer[1])[0][0] * 100  # Convert to 0-100 scale
    
    # Weighted similarity score
    final_score = (fuzz_ratio * 0.3) + (token_sort_ratio * 0.3) + (tfidf_sim * 0.4)  # Adjust weights as needed
    return final_score

def search_pubmed(title, similarity_threshold=80):
    """
    Searches PubMed for a given paper title and retrieves its full-text URL if available.
    Uses fuzzy matching to find the best match.
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Step 1: Use double quotes to enforce exact phrase search
    query = f'"{title}"'
    esearch_url = f"{base_url}esearch.fcgi?db=pubmed&term={quote(query)}&retmode=json"
    
    response = requests.get(esearch_url)
    response.raise_for_status()
    search_data = response.json()
    
    # Get list of PMIDs
    id_list = search_data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return f"No results found for '{title}'"
    
    best_match = None
    best_score = 0

    # Step 2: Loop through results to find the most similar title
    for pmid in id_list:
        # print(pmid)
        efetch_url = f"{base_url}esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        response = requests.get(efetch_url)
        response.raise_for_status()
        metadata = response.json()

        article_data = metadata.get("result", {}).get(pmid, {})
        found_title = article_data.get("title", "").strip()
        
        # Compute similarity score
        similarity_score = calculate_title_similarity(title, found_title)
        
        # Update best match if the score is higher
        if similarity_score > best_score and similarity_score >= similarity_threshold:
            best_score = similarity_score
            best_match = {
                "title": found_title,
                "pmid": pmid,
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "full_text_url": None
            }

            # Extract DOI or Full-Text link if available
            if "articleids" in article_data:
                for item in article_data["articleids"]:
                    if item["idtype"] == "doi":
                        best_match["full_text_url"] = f"https://doi.org/{item['value']}"

    return best_match if best_match else "No similar title found above threshold."



def retrieve_html(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None  # Handle failed request

    soup = BeautifulSoup(response.text, 'html.parser')
    # print(soup)
    return soup


def query_gpt(html):
    prompt = """
Below is a web page html I scraped from a publication website. The article may not be present because the website blocks scraping or due to any other error.
If you identify the article is successfully scraped as below, retrieve the full text of the paper from the following html. And put each section of the article into a key-value pair inside a JSON object.
Below is an example output format, the parameters are not limited to those listed below. If the article is not present, simply returns an empty JSON. Take note: Only return the JSON object.
\"{"title": "",
 "abstract": "",
 "background": "",
 "method": "",
 "result": "",
 "discussion": "",
 ...}\"

 ###{HTML Web Page}:

"""
    prompt += f"{html}"

    model_resp = try_gpt_4(prompt)
    print(model_resp)
    return model_resp


def get_full_text_from_url(url):
    """
    Uses Selenium to resolve DOI redirects, scrape the full-text content of an article page.
    """

    # Configure Selenium Options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")  # Fix DevToolsActivePort issue
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Enable cookies to bypass login restrictions
    chrome_prefs = {
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": False,
    }
    chrome_options.add_experimental_option("prefs", chrome_prefs)

    # Define ChromeDriver path (update this with the correct path)
    webdriver_service = Service('D:\\chromedriver-win64\\chromedriver.exe')

    # Start WebDriver
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    try:
        print(f"[INFO] Opening {url}...")
        driver.get(url)

        # Wait for redirect to the actual article page
        time.sleep(5)  # Generic wait for JavaScript-rendered content
        final_url = driver.current_url  # Get the resolved URL after redirection
        print(f"[INFO] Resolved final article URL: {final_url}")

        # Check if we are blocked
        if "Your browser is outdated" in driver.page_source or "update your browser" in driver.page_source:
            print("[ERROR] The publisher is blocking Selenium. Try using a real browser.")
            driver.quit()
            return retrieve_html(final_url)

        # Try waiting for an article section to load (modify as needed)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
        except:
            print("[WARNING] Could not locate <article> element, extracting all content.")

        # Get fully rendered page source
        page_source = driver.page_source

        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract full text content from recognized sections
        # sections = {
        #     "final_url": final_url,
        #     "title": None,
        #     "abstract": None,
        #     "body": None
        # }

        # # Find title
        # title_tag = soup.find("h1") or soup.find("title")
        # sections["title"] = title_tag.get_text(strip=True) if title_tag else "Title not found"

        # # Find abstract
        # abstract_tag = soup.find("div", class_="abstract") or soup.find("section", class_="Abstract")
        # sections["abstract"] = abstract_tag.get_text(strip=True) if abstract_tag else "Abstract not found"

        # # Find full body content
        # body_tag = soup.find("div", class_="article-body") or soup.find("article") or soup.find("main")
        # sections["body"] = body_tag.get_text(strip=True) if body_tag else "Full text not found"

        # driver.quit()
        return soup

    except Exception as e:
        driver.quit()
        print(f"[ERROR] Failed to retrieve full-text: {e}")
        return None


if __name__ == "__main__":
    file = open("data\\gpt2_11.txt", "r", encoding="utf-8")
    # output_file = open("data\\fulltext_11.txt", "w+", encoding="utf-8")
    content = file.readlines()
    total_num = len(content) - 1
    has_full_text_num = 0
    for line in content:
        paper_title = line.split(";")[0].strip()
        if paper_title.endswith("."):
            paper_title = paper_title[:-1]
        result = search_pubmed(paper_title)

        if type(result) is dict:
            has_full_text_num += 1
            url = result["full_text_url"]
            html = get_full_text_from_url(url)
            # print(html)
            fulltext = query_gpt(html)
            # output_file.write(fulltext+"\n\n")

        else:
            pass
            # output_file.write(f"{paper_title} is not available.\n\n")