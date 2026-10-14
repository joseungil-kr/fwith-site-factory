"""Frozen A04 mechanical helpers; no automatic semantic verdicts."""
import html, re, unicodedata

VALUES = {'T1': [0,5,10], 'T2': [0,5,10], 'T3': [0,10], 'T4': [0,5,10],
          'H1': [0,7,15], 'H2': [0,5,10], 'A1': [0,5,15], 'A2': [0,5,10], 'I1': [0,5,10]}

def normalize(text):
    return ' '.join(unicodedata.normalize('NFC', html.unescape(text)).split())

def lexical_map(text):
    n = normalize(text)
    chars, offsets = [], []
    for i, char in enumerate(n):
        for lower in char.casefold():
            if unicodedata.category(lower)[0] in ('L','N'):
                chars.append(lower)
                offsets.append(i)
    return ''.join(chars), offsets

def lexical_candidates(text, phrase):
    haystack, mapping = lexical_map(text)
    needle, _ = lexical_map(phrase)
    if not needle:
        return []
    out, start = [], 0
    while True:
        found = haystack.find(needle, start)
        if found < 0:
            break
        out.append([mapping[found], mapping[found+len(needle)-1]+1])
        start = found+1
    return out

def opening_windows(text):
    n = normalize(text)
    return {'normalized':n, 'first_120':n[:120], 'first_180':n[:180]}

def front_placement(title, combination_span):
    n = normalize(title)
    # Separators operate on normalized title, except the first raw newline,
    # whose location is found by normalizing the preceding raw text.
    separators = [m.start() for m in re.finditer(r'[|｜:：–—]|(?<= )-(?= )', n)]
    for m in re.finditer(r'\r\n|\r|\n', title):
        separators.append(len(normalize(title[:m.start()])))
    first = min(separators) if separators else None
    limit = (len(n)+1)//2
    valid_span = combination_span is not None and 0 <= combination_span[0] < combination_span[1] <= len(n)
    ok = valid_span and combination_span[0] < limit and (first is None or combination_span[1] <= first)
    return {'length':len(n), 'midpoint_exclusive':limit, 'first_separator':first,
            'span':combination_span, 'front_test':bool(ok)}

def calculate(rows, mandatory_violations=(), evidence_unverified=False):
    if set(rows) != set(VALUES):
        raise ValueError('Provide exactly the nine preregistered row IDs')
    for row, value in rows.items():
        if value is not None and (type(value) is not int or value not in VALUES[row]):
            raise ValueError('Unpermitted points for '+row)
    if any(g not in ('G1','G2','G3','G4','G5') for g in mandatory_violations):
        raise ValueError('Only G1–G5 are numeric ceiling gates')
    low = sum(v for v in rows.values() if v is not None)
    high = low+sum(max(VALUES[k]) for k,v in rows.items() if v is None)
    unknown = any(v is None for v in rows.values()) or evidence_unverified
    effective = [min(low,89),min(high,89)] if mandatory_violations else [low,high]
    if unknown:
        verdict = 'A04_UNVERIFIED'
    elif mandatory_violations or effective[0] < 90:
        verdict = 'A04_ALIGNMENT_REVISE'
    else:
        verdict = 'A04_ALIGNMENT_MEETS_INTERNAL_THRESHOLD'
    return {'raw_score':None if unknown else low,'known_rows_subtotal':low,'possible_raw_range':[low,high],
            'effective_score':None if unknown else effective[0], 'possible_effective_range':effective,
            'numeric_ceiling':89 if mandatory_violations else None,'gates':list(mandatory_violations),
            'verdict':verdict}
