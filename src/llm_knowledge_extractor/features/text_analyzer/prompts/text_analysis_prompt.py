

text_analysis_prompt = """You are an expert text analyst. Analyze the provided text and return your analysis as valid JSON with exactly this structure:

{{
    "summary": "A concise 1-2 sentence summary capturing the main point",
    "title": "A descriptive title for the text (or null if no clear title can be determined)",
    "topics": ["topic1", "topic2", "topic3"],
    "sentiment": "positive|neutral|negative",
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}

Requirements:
- summary: Must be 1-2 sentences maximum, capturing the core message
- title: Extract existing title or create a descriptive one; use null if text is too fragmented
- topics: Identify exactly 3 key themes, subjects, or topics discussed
- sentiment: Classify overall emotional tone as "positive", "neutral", or "negative"
- keywords: Extract exactly 3 most important/frequent nouns or key terms from the text

Return ONLY the JSON object with no additional text, explanations, or markdown formatting.

Text to analyze:
{text}"""

system_prompt = "You are a helpful text analysis assistant. Always respond with valid JSON only."


