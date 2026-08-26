# Jarvis Personality Evaluation

Use this prompt set manually after changes to the personality prompt. Do not
assert exact LLM text in unit tests.

Score each response from 1 to 5 for accuracy, naturalness, brevity, Indian feel,
humor fit, language matching, serious-context handling, and voice friendliness.
Also note whether the answer used too much slang or became too verbose.

## English

- What is the capital of Australia?
- Explain a black hole simply.
- What is 10 divided by 2?
- Why do we sleep?
- Tell me something interesting.
- Explain quantum computing simply.
- What's the difference between RAM and storage?
- Give me a quick productivity tip.

## Hinglish

- Bhai black hole kya hota hai?
- Kal Monday hai kya?
- Yaar quantum computing simple language mein samjha.
- Ye API actually kaise kaam karti hai?
- Bhai kuch interesting bata.
- Jarvis kya scene hai?
- Simple bol, Docker image kya hoti hai?
- Aaj coding ka mood nahi hai, kya karun?

## Hindi

- भारत की राजधानी क्या है?
- ब्लैक होल क्या होता है?
- आज कुछ अच्छा बताओ।
- नींद क्यों जरूरी होती है?
- कंप्यूटर मेमोरी क्या होती है?

## Humor

- What is 2 plus 2?
- Kal Monday hai?
- I slept at 4 AM and woke up at 8.
- I opened Instagram for five minutes and wasted two hours.
- I spent one hour choosing a font.

## Serious Context

- I'm feeling really low today.
- I'm worried about my job.
- My friend had an accident.
- I think something might be seriously wrong.
- I made a big mistake at work and I feel awful.

## Unsupported Actions

- Turn off my bedroom light.
- Set an alarm for 7 AM.
- What's the weather outside right now?
- Send a WhatsApp message to Rahul.
- Remind me tomorrow morning to call my bank.

## Repetition Check

Ask five unrelated prompts in a row and watch for repeated fillers such as
`bhai`, `haan ji`, `yaar`, `boss`, or `easy one`.

## Voice Readability Check

Read each response aloud. Flag headings, heavy markdown, long parentheticals,
and list-heavy answers that would sound awkward in TTS.
