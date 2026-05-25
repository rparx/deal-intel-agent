import os
import yaml
import feedparser

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

from send_email import send_email

# Load environment variables
load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load config
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

def clean_text(text):
    return BeautifulSoup(text or "", "html.parser").get_text()

def summarize_article(title):

    prompt = f"""
    You are an elite private equity investment analyst.

    Analyze this headline like an investor preparing for an investment committee meeting.

    Headline:
    {title}

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

for industry in config["industries"]:

    print(f"\n=== {industry['name']} ===")

    for source in industry["sources"]:

        feed = feedparser.parse(source)

        for entry in feed.entries[:3]:

            title = clean_text(entry.get("title", ""))
            link = entry.get("link", "")

            print(f"\nARTICLE: {title}")
            print(link)

            summary = summarize_article(title)

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