# src/extractor/prompts.py
# All LLM prompt templates in one place
# Each function takes text input and returns final prompt string
#
# Hallucination prevention techniques applied to every prompt:
#   1. temperature = 0.0 in config.yaml
#   2. Explicit JSON schema shown
#   3. "ONLY extract what is written" instruction
#   4. Concrete positive example
#   5. Explicit negative example
#   6. Empty list/string for missing data
#   7. One task per prompt — never combine


def skills_prompt(content):
    """
    Prompt for extracting skills from resume.

    Args:
        content (str): Resume skills section or full text

    Returns:
        str: Final prompt
    """
    return f"""You are a resume parser.

Extract ALL professional skills explicitly written in the resume text.

RULES:
- Extract ONLY skills explicitly written in the text
- NEVER invent or infer skills
- Include technical skills, tools, software, methodologies, and domain skills
- Do NOT include job titles, companies, or responsibilities
- Convert all skills to lowercase
- Remove duplicates
- Return ONLY valid JSON
- First character must be [

SKILL TYPES MAY INCLUDE:
- technical skills (python, sql, aws)
- software/tools (excel, sap, tableau)
- professional skills (project management, negotiation)
- domain skills (financial analysis, seo, digital marketing)
- methodologies (agile, scrum, six sigma)

EXAMPLE OUTPUT:[python", "sql", "aws", "project management", "financial analysis", "seo", "customer relationship management" ]

IF NO SKILLS FOUND RETURN: []

TEXT:
{content}

JSON:
"""


def experience_prompt(content):
    """
    Prompt for extracting work experience from resume.

    Args:
        content (str): Resume experience section or full text

    Returns:
        str: Final prompt
    """
    return f"""You are a resume parser. Extract all work experience from the text below.

    RULES:
    - Extract ONLY jobs explicitly written in the text
    - NEVER invent job titles, companies or responsibilities
    - If two jobs have overlapping dates only count the period once — do NOT double count overlapping time
    - e.g. Job A: Jan 2020 - Dec 2022 (3 years) and Job B: Jun 2022 - Jun 2023 (1 year) overlap is Jun 2022 - Dec 2022 (0.5 years) so total = 3 + 0.5 = 3.5 years NOT 4 years
    - Calculate duration_years from dates if present — e.g. Jan 2022 to Jun 2023 = 1.5
    - If dates are missing set duration_years to 0
    - Summarize the all responsibities bullet points into 2-3 lines.
    - Return ONLY valid JSON array — no explanation, no markdown
    - First character must be [

    EXAMPLE OUTPUT:[
    {{
        "title": "Data Scientist",
        "company": "Acme Corp",
        "duration_years": 2.5,
        "responsibilities": [ "Built machine learning models to predict churn", "Reduced model inference time by 40%"
        ]
    }}
    ]

    IF NO EXPERIENCE FOUND return: []

    TEXT:
    {content}

    JSON:"""


def education_prompt(content):
    """
    Prompt for extracting education from resume.

    Args:
        content (str): Resume education section or full text

    Returns:
        str: Final prompt
    """
    return f"""You are a resume parser. Extract all education and degrees from the text below.

RULES:
- Extract ONLY degrees explicitly written in the text
- NEVER invent degrees, universities or fields
- Normalise degree to: PhD, MSc, MBA, BSc, BEng, MEng, Diploma
- Use full field name — e.g. "Data Science and Statistics" not just "Data"
- Return ONLY valid JSON array — no explanation, no markdown
- First character must be [

EXAMPLE OUTPUT:
[
  {{
    "degree": "MSc",
    "field": "Data Science and Machine Learning",
    "university": "University of Edinburgh"
  }}
]

IF NO EDUCATION FOUND return: []

TEXT:
{content}

JSON:"""


def languages_prompt(content):
    """
    Prompt for extracting spoken languages from resume.

    Args:
        content (str): Resume languages section

    Returns:
        str: Final prompt
    """
    return f"""You are a resume parser. Extract all spoken/written human languages from the text below.

RULES:
- Extract ONLY languages explicitly written in the text
- NEVER invent or assume languages
- Return language names in lowercase
- Do NOT include programming languages like Python or SQL
- Return ONLY valid JSON array — no explanation, no markdown
- First character must be [

EXAMPLE OUTPUT:
["english", "german", "french"]

IF NO LANGUAGES FOUND return: []

TEXT:
{content}

JSON:"""


def title_prompt(content):
    """
    Prompt for extracting most recent job title from resume.

    Args:
        content (str): First 500 chars of resume

    Returns:
        str: Final prompt
    """
    return f"""You are a resume parser. What is the most recent job title in this resume?

RULES:
- Return ONLY the job title - nothing else
- NEVER invent or guess if not present
- If no job title found return: Unknown

EXAMPLE OUTPUT:
Senior Data Scientist

TEXT:
{content}

TITLE:"""


def jd_prompt(content):
    """
    Prompt for extracting structured requirements from job description.

    Args:
        content (str): Full job description text

    Returns:
        str: Final prompt
    """
    return f"""You are a job description parser. Extract all requirements from the text below.

RULES:
- Extract ONLY what is explicitly written in the job description
- NEVER invent, guess or infer requirements not present
- If a field has no data return empty list [] or empty string ""
- Split compound skills into individual items
- Return ONLY valid JSON — no explanation, no markdown
- First character must be {{

FIELD RULES:
- required_skills: hard technical must-have skills e.g. Python, SQL, AWS
- preferred_skills: domain knowledge, nice-to-have e.g. actuarial, insurance, finance
- required_years_experience: integer or 0 if not specified
- required_education.degree: masters | bachelors | phd | diploma | "" if not specified
- required_languages: spoken languages only e.g. english, german
- responsibilities: copy bullet points exactly from JD
- nice_to_have: bonus qualifications, extra certifications

SPLITTING RULES:
- "actuarial (reserving, pricing, risk)" → ["actuarial", "reserving", "pricing", "risk"]
- "Python/R/SQL" → ["python", "r", "sql"]
- All required_skills and preferred_skills must be lowercase

EXAMPLE OUTPUT:
{{
  "job_title": "Senior Data Scientist",
  "required_skills": ["python", "sql", "aws"],
  "preferred_skills": ["actuarial", "insurance"],
  "required_years_experience": 5,
  "required_education": {{
    "degree": "masters",
    "field": "Data Science or Statistics"
  }},
  "required_languages": ["english"],
  "responsibilities": [
    "Build and deploy machine learning models",
    "Collaborate with stakeholders to define requirements"
  ],
  "nice_to_have": ["phd", "spark", "databricks"]
}}

TEXT:
{content}

JSON:"""