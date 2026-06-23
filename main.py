import os
import yaml
import feedparser
from db import save_article

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

from send_email import send_email

import requests

def fetch_article_text(url):
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join(
            p.get_text(strip=True)
            for p in paragraphs
        )

        return text[:5000]

    except Exception as e:
        print(f"Error fetching article text: {e}")
        return ""

# Load environment variables
load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load config
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

def clean_text(text):
    return BeautifulSoup(text or "", "html.parser").get_text()

def summarize_article(title, article_text):

    prompt = f"""
    You are an elite private equity investment analyst.

    Analyze this headline like an investor preparing for an investment committee meeting.

    Article Title:
    {title}

    Article Text:
    {article_text}

    Return your response in this exact format:

    SUMMARY:
    2 concise sentences explaining the development.

    WHY IT MATTERS:
    Explain the strategic or operational importance.

    INVESTING IMPLICATIONS:
    Focus on:
    - market structure
    - competitive dynamics
    - operational implications
    - margin implications
    - AI/automation implications if relevant
    - M&A or consolidation implications if relevant

    DILIGENCE QUESTION:
    Include 1 highly insightful diligence question an investor should ask.
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def score_article(title, article_text, watchlist_name, keywords, companies):
                prompt = f"""
            You are a private equity investor evaluating whether a news article is relevant.

            Score this article from 1 to 10 for relevance to:

            - AI-enabled services
            - AI roll-ups
            - workflow automation
            - operational transformation
            - fragmented services industries
            - PE value creation
            - margin expansion
            - acquisitions / consolidation

            Watchlist:
            {watchlist_name}

            Target keywords:
            {keywords}

            Target companies:
            {companies}

            Article title:
            {title}

            Article text:
            {article_text}

            Scoring guide:
            10 = directly about AI-enabled services acquisition / roll-up
            9 = PE/VC investment in AI workflow company
            8 = operational automation with clear margin implications
            7 = industry-specific workflow transformation
            5 = general AI news
            3 = broad macro or generic company news
            1 = irrelevant or sponsored fluff

            Articles involving acquisitions of service businesses should receive a higher score.

            Return only a single number.
            """

                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )

                try:
                    return int(response.choices[0].message.content.strip())
                except:
                    return 0

def extract_article_metadata(title, article_text, watchlist_name):
    prompt = f"""
You are extracting structured metadata from an article for a private equity market intelligence database.

Article title:
{title}

Watchlist:
{watchlist_name}

Article text:
{article_text}

Return ONLY valid JSON with this exact structure:

{{
  "companies": ["Company 1", "Company 2"],
  "themes": ["Theme 1", "Theme 2"],
  "article_type": "capital_flow"
}}

Rules:
- companies should include companies, investors, sponsors, or platforms mentioned
- themes should be concise tags like "AI roll-up", "workflow automation", "healthcare RCM", "margin expansion", "M&A", "operational transformation"
- article_type must be one of:
  - capital_flow
  - acquisition
  - operational_transformation
  - thought_leadership
  - industry_signal
  - regulatory_signal
  - funding
  - product_launch
  - other
- Return JSON only. No markdown. No explanation.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    try:
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Metadata extraction failed: {e}")
        return {
            "companies": [],
            "themes": [],
            "article_type": "other"
        }

def generate_morning_brief(article_summaries):

    combined_text = "\n\n".join(article_summaries)

    prompt = f"""
    You are preparing a morning intelligence brief for a private equity investor focused on:
    - operational improvement
    - AI transformation
    - healthcare
    - fragmented industries
    - roll-ups
    - workflow automation
    - market structure shifts

    Based on these article summaries:

    {combined_text}

    Create a concise, highly insightful morning brief.

    Include:

    TOP TAKEAWAYS
    - 3-5 bullets
    - only the most important insights

    EMERGING THEMES
    - identify patterns across articles
    - explain WHY they matter

    INVESTING IMPLICATIONS
    - implications for PE-backed businesses
    - operational implications
    - AI/workflow implications
    - margin implications
    - consolidation implications

    WHAT TO WATCH
    - important future signals
    - regulatory shifts
    - operational bottlenecks
    - technological inflection points

    BEST DILIGENCE QUESTIONS
    - 3-5 highly insightful investor questions

    Make it:
    - concise
    - sharp
    - non-generic
    - intellectually differentiated
    - easy to skim
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

all_summaries = []

for industry in config["watchlists"]:

    print(f"\n=== {industry['name']} ===")

    for source in industry["sources"]:

        feed = feedparser.parse(source)
        print(f"\nSource: {source}")
        print(f"Entries found: {len(feed.entries)}")

        for entry in feed.entries[:3]:

            title = clean_text(entry.get("title", ""))
            link = entry.get("link", "")

            print(f"\nARTICLE: {title}")
            print(link)

            
            rss_summary = clean_text(entry.get("summary", ""))

            full_article_text = fetch_article_text(link)

            article_text = full_article_text if full_article_text else rss_summary

            score = score_article(
                title=title,
                article_text=article_text,
                watchlist_name=industry["name"],
                keywords=industry.get("keywords", []),
                companies=industry.get("companies", [])
            )

            print(f"Relevance score: {score}")

            source_type = industry.get("source_type", "news")

            if source_type == "thought_leadership":
                threshold = 5
            else:
                threshold = 7

            if score < threshold:
                print("Skipping low-relevance article.")
                continue

            summary = summarize_article(
                title,
                article_text
            )
            
            metadata = extract_article_metadata(
                title=title,
                article_text=article_text,
                watchlist_name=industry["name"]
)

            article_record = {
                "industry": industry["name"],
                "source": source,
                "title": title,
                "url": link,
                "summary": summary,
                "relevance_score": score,
                "companies": ", ".join(metadata.get("companies", [])),
                "themes": ", ".join(metadata.get("themes", [])),
                "article_type": metadata.get("article_type", "other"),
                "sent_in_brief": True
            }

            save_article(article_record)

            formatted_summary = f"""
ARTICLE: {title}

LINK: {link}

SUMMARY:
{summary}
"""

            all_summaries.append(formatted_summary)

            print("\nAI SUMMARY:")
            print(summary)
            print("\n" + "=" * 50)

print("\n\n")
print("GENERATING MORNING BRIEF...")
print("\n")

morning_brief = generate_morning_brief(all_summaries)

print(morning_brief)

print("\nSENDING EMAIL...\n")

send_email(
    subject="Morning Intelligence Brief",
    content=morning_brief
)

print("\nDONE.\n")