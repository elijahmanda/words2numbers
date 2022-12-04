import re
from copy import copy
from .ejtoken import tokenize as _tokenize, detokenize as _detokenize

from .utils import text_span_replace
from .data import TEN_HYPHEN_ONE, SKIP_HUNDRED_1, SKIP_HUNDRED_2, SKIP_HUNDRED_3
    
def _normalize_ten_hyphen_one(text: str):
    """ normalize numbers such as: "twenty-five" to "twenty five", "seventy-nine" to "seventy nine" """
    
    rtokens = []
    tokens = _tokenize(text)
    for n in tokens:
        if TEN_HYPHEN_ONE.match(n):
            t1, t2 = n.split("-")
            rtokens.extend([t1, t2])
        else:
            rtokens.append(n)
    return _detokenize(rtokens)

def _normalize_skip_hundreds_1(text: str) -> str:
    """ normalize numbers such as: "one thirty" to "one hundred thirty", "six seventy" to "six hundred seventy" 
    Usually this normalization step must come before ``"""
    reps = []
    rttext = copy(text)
    for match in SKIP_HUNDRED_1.finditer(rttext):
        one_1, teen_0 = match.group().split()
        replaced = f"{one_1} hundred {teen_0}"
        reps.append((replaced, match.span()))
    counter=0
    if reps:
        for rep, sp in reps:
            rttext = text_span_replace(rttext, rep, (sp[0]+counter, sp[1]+counter))
            counter+=8
    return rttext

def _normalize_skip_hundreds_2(text: str) -> str:
    """ normalize numbers such as: "one thirty" to "one hundred thirty", "six seventy" to "six hundred seventy" 
    Usually this normalization step must come before ``"""
    reps = []
    rttext = copy(text)
    for match in SKIP_HUNDRED_2.finditer(rttext):
        one_1, ten_0 = match.group().split()
        replaced = f"{one_1} hundred {ten_0}"
        reps.append((replaced, match.span()))
    counter=0
    if reps:
        for rep, sp in reps:
            rttext = text_span_replace(rttext, rep, (sp[0]+counter, sp[1]+counter))
            counter+=8
    return rttext


def _normalize_skip_hundreds_3(text: str) -> str:
    """ normalize numbers such as: "one twenty five" to "one hundred twenty five", "six seventy nine" to "six hundred seventy nine" 
    Usually this normalization step must come before `_normalize_skip_hundres_2`"""
    reps = []
    rttext = copy(text)
    for match in SKIP_HUNDRED_3.finditer(rttext):
        one_1, ten_0, one_2 = match.group().split()
        replaced = f"{one_1} hundred {ten_0} {one_2}"
        reps.append((replaced, match.span()))
    counter=0
    if reps:
        for rep, sp in reps:
            rttext = text_span_replace(rttext, rep, (sp[0]+counter, sp[1]+counter))
            counter+=8
    return rttext

def _rep_commas(text):
    for m in re.finditer(r"[^\d],", text):
        st, end = m.span()
        text = text_span_replace(text, " ", (st+1, end))
    return text

def _possible_range(text):
    for m in re.finditer(r"\d\-\d", text):
        st, end = m.span()
        text = text_span_replace(text, " ", (st+1, end-1))
    return text

class Pipe:
    
    def __init__(self):
        self._pipes = (
            # normalize multiple spaces
            lambda text: re.sub(r"\s{2,}", " SPACE ", text),
            # normalize preceding commas to avoid detecting nA,,nB as nA nB (ie as one) but nA, nB (ie two seperate numbers)
            lambda text: re.sub(r",\s{,}?,", " COMMA ", text),
            #replace commas
            _rep_commas,
            # normalize where numbers may express a possible range eg 2-3; this may be 2 minus 3, or 2 to 3 to avoid false negatives we remove the hyphen
            _possible_range,
            # normalize hyphen concentrated numbers
            _normalize_ten_hyphen_one,
            #_normalize_skip_hundreds_1,
            #_normalize_skip_hundreds_3,
            #_normalize_skip_hundreds_2,
        )
    
    def __call__(self, text: str) -> str:
        for pipe in self._pipes:
            text = pipe(text)
        return text