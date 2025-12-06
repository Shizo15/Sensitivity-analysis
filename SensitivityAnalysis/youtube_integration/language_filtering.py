# methods for filtering comments into en and non-en
# each method returns a tuple (english_comments, non_english_comments, stats_dict)

import time
import math

from langdetect import detect_langs, LangDetectException
import langid
import pycld2 as cld2

CONFIDENCE_THRESHOLD = 0.90


# LANGDETECT
def filter_lang_langdetect(comments):
    start = time.time()
    en = []
    non_en = []

    for c in comments:
        try:
            langs = detect_langs(c)
            top = langs[0]
            lang = top.lang
            prob = top.prob

            if lang == "en" and prob >= CONFIDENCE_THRESHOLD:
                en.append(c)
            else:
                non_en.append(c)

        except LangDetectException:
            non_en.append(c)

    return en, non_en, {
        "method": "langdetect",
        "english": len(en),
        "non_english": len(non_en),
        "time": round(time.time() - start, 3),
    }


# LANGID
def filter_lang_langid(comments):
    start = time.time()
    en = []
    non_en = []

    for c in comments:
        try:
            lang, logprob = langid.classify(c)  # logprob = ln(p)
            prob = math.exp(logprob)           # próbujemy odzyskać p z log(p)

            if lang == "en" and prob >= CONFIDENCE_THRESHOLD:
                en.append(c)
            else:
                non_en.append(c)
        except Exception:
            non_en.append(c)

    return en, non_en, {
        "method": "langid",
        "english": len(en),
        "non_english": len(non_en),
        "time": round(time.time() - start, 3),
    }


# CLD2
def filter_lang_cld2(comments):
    start = time.time()
    en = []
    non_en = []

    for c in comments:
        try:
            reliable, textBytesFound, details = cld2.detect(c)
            # details[0] = (language_name, language_code, percent, score)
            lang_code = details[0][1]
            percent = details[0][2]
            prob = percent / 100.0

            if lang_code == "en" and prob >= CONFIDENCE_THRESHOLD and reliable:
                en.append(c)
            else:
                non_en.append(c)

        except Exception:
            non_en.append(c)

    return en, non_en, {
        "method": "cld2",
        "english": len(en),
        "non_english": len(non_en),
        "time": round(time.time() - start, 3),
    }
