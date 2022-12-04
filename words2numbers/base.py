from __future__ import annotations

import re
from copy import copy
from typing import Tuple, List, Union, NoReturn, Dict, Any

from loguru import logger
from time import perf_counter

from .data import (
    ONES,
    ORDINAL_ONES,
    ORDINALS,
    TEENS_AND_TEN,
    TENS,
    MULTIPLES,
    ALL_NUMS,
    ALL_VALID,
    ANDS,
    POINTS,
    ZEROS,
    NEGATIVES,
    MIXED_SPOKEN_REGEX,
    ANY_NUMBER_REGEX,
    NUMBER_FOLLOWED_BY_POWER_REGEX,
    NUMBER_FOLLOWED_BY_SUFFIX_REGEX,
    DOT_ANY_NUMBER_REGEX,
    INFORMALS_EXACT_REGEX,
    INFORMALS_MULTIPLYABLE_REGEX,
    ORDINAL_NUMERAL_REGEX
)
from words2numbers.normalize import Pipe
from words2numbers.utils import text_span_replace, count_spaces
from words2numbers.ejtoken import tokenize
from ._words2num import _words2num

logger.disable(__name__)

class CompStr:
    def __init__(self, string: str):
        self._string = string

    @property
    def is_point(self):
        return self._string in POINTS

    @property
    def is_num_word(self):
        
        return self._string in ALL_VALID

    @property
    def is_and(self):
        return self._string in ANDS

    @property
    def is_ordinal(self):
        return self._string in ORDINALS

    def __str__(self):
        return self._string
        
    def __lt__(self, val):
        return False

    def __gt__(self, val):
        return False

    def __ge__(self, val):
        return False

    def __le__(self, val):
        return False

    def __eq__(self, val):
        return self._string == val

    def __hash__(self):
        return hash((self._string, self.is_and, self.is_num_word, self.is_point))


class ModInt(int):
    def __init__(self, *args):
        self._is_ordinal = False
        
    @property
    def is_point(self):
        return False

    @property
    def is_num_word(self):
        return True

    @property
    def is_and(self):
        return False

    @property
    def is_ordinal(self):
        return self._is_ordinal
    
    @is_ordinal.setter
    def is_ordinal(self, val: bool):
        self._is_ordinal = val


@logger.catch
def _get_prev(c: Tuple[int], idx: int) -> Union[int, CompStr]:
    c_len = len(c)
    if idx == 0 or idx > c_len-1:
        return CompStr("always-big")
    try:
        return c[idx-c_len-1]
    except IndexError:
        return CompStr("always-big")

@logger.catch
def _get_next(container: Tuple[int], index: int) -> Union[int, CompStr]:
    try:
        return container[index+1]
    except IndexError:
        return CompStr("none")

@logger.catch
def is_multiple1000(number: int) -> bool:
    return number and number != 100 and IN(number, "multiples")
    
def IN(number: int, *categories: Tuple[str]) -> bool:
    contains = True
    # remove duplicates
    categories = set(categories)
    if not categories:
        contains = False
    cat = {
        "ones": ONES.values(),
        "teens": TEENS_AND_TEN.values(),
        "tens": TENS.values(), "multiples": MULTIPLES.values()
    }
    for key in categories:
        contains &= list(cat[key]).__contains__(number)
    return contains
    
@logger.catch
def _get_idxs_from_bool(bool_container: Tuple[bool]) -> List[List[int]]:
    built_idxs = []
    for i, truth in enumerate(bool_container):
        if not truth:
            built_idxs.append(i)
    return built_idxs

@logger.catch
def _get_numbers_from_idxs(numbers: Tuple[Union[int, str]], idxs: Tuple[int]) -> Tuple[List[List[int]], List[Tuple[int,int]]]:
    prev_idx = 0
    rtidxs = []
    nums = []
    for end in idxs:
        nums.append(numbers[prev_idx:end+1])
        rtidxs.append((prev_idx, end+1))
        prev_idx = end+1
    return nums, rtidxs

def _check_and_point(numbers: Tuple[Union[int, str]]) -> Tuple[Tuple[bool], Tuple[Tuple[int, int]]]:
    bool_container: List[bool] = []
    idx_container: List[Tuple[int, int]] = []
    
    prev_multiple = CompStr("always-big")
    prev_point = False
    and_sep = False
    prev_false_truth = True
    beginning = True
    index = 0
    
    def make_order(val: str) -> CompStr | ModInt:
        is_ordinal = False
        if val in ORDINALS:
            is_ordinal = True
        num_ = ALL_NUMS.get(val)
        if num_:
            val = num_
        if isinstance(val, str):
            val = CompStr(val)
        if isinstance(val, (int, float)):
            modint = ModInt(val)
            modint.is_ordinal = is_ordinal
            return modint
        return val

    
    def add_to_con(truth: bool, idx: int=None) -> NoReturn:
        nonlocal bool_container, prev_multiple, prev_point, and_sep, index, idx_container, prev_false_truth, beginning
        if not truth:
            prev_multiple = CompStr("always-big")
            prev_point = False
            and_sep = False
            prev_false_truth = True
            beginning =True
        else:
            prev_false_truth = False
            beginning = False
        bool_container.append(truth)
        idx_container.append((index, idx))
        index = idx
    
    for i, num in enumerate(numbers):
        next_num = make_order(_get_next(numbers, i))
        nnext_num = make_order(_get_next(numbers, i+1))
        prev_num = make_order(_get_prev(numbers, i))
        pprev=make_order(_get_prev(numbers, i-1))
        num = make_order(num)
        
        # Check if its valid such that `number` or `and` or `point`
        if not num.is_num_word:
            add_to_con(False, i)
            
        # nothing can come next after an ordinal
        
        elif num.is_ordinal:
            add_to_con(False, i)
        
        elif next_num.is_point and not IN(nnext_num, "ones"):
            add_to_con(False, i)
        
        elif num in NEGATIVES:
            if (next_num in ALL_NUMS.values()) and beginning:
                add_to_con(True)
            else:
                add_to_con(False)
        
        elif prev_num==100 and next_num==100 and not is_multiple1000(num):
            add_to_con(False, i)
        
        elif is_multiple1000(num) and next_num>=num:
            add_to_con(False, i)
        
        elif num.is_and:
            and_sep = True
            if (not prev_num.is_num_word) or prev_num.is_and or prev_num.is_point:
                add_to_con(False, i)
            elif IN(next_num, "ones"):
                add_to_con(True)
            elif IN(next_num, "teens"):
                add_to_con(True)
            elif IN(next_num, "tens"):
                add_to_con(True)
            else:
                add_to_con(False, i)
                and_sep = False
                
        elif num.is_point:
            if IN(next_num, "ones"):
                add_to_con(True)
                prev_point = True
            else:
                add_to_con(False, i)
        
        elif num>=prev_multiple:
            add_to_con(False, i)
            
        elif next_num>=prev_multiple:
            add_to_con(False, i)
            
        elif IN(num, "ones"):
            if prev_point:
                if IN(next_num, "ones"):
                    add_to_con(True)
                else:
                    add_to_con(False, i)
            elif pprev==100 and prev_num.is_and and next_num==100:
                add_to_con(False)
            elif not prev_point and next_num.is_point:
                add_to_con(True)
            elif num == 0:
                if IN(next_num, "ones") or prev_point:
                    add_to_con(True)
                else:
                    add_to_con(False, i)
            elif IN(prev_num, "tens") and next_num==100:
                add_to_con(False)
            elif is_multiple1000(next_num):
                add_to_con(True)
            elif IN(next_num, "multiples"):
                add_to_con(True)
            elif next_num.is_and:
                add_to_con(False, i)
            else:
                add_to_con(False, i)
                
        elif IN(num, "teens"):
            if is_multiple1000(next_num):
                add_to_con(True)
            elif next_num.is_point:
                add_to_con(True)
            else:
                add_to_con(False, i)
                
        elif IN(num, "tens"):
            if IN(next_num, "ones"):
                add_to_con(True)
            # ordinals
            elif ORDINAL_ONES.get(next_num):
                add_to_con(True)
            elif is_multiple1000(next_num):
                add_to_con(True)
            elif next_num.is_point:
                add_to_con(True)
            else:
                add_to_con(False, i)
        
        elif is_multiple1000(num):
            prev_multiple = num
            if next_num.is_point:
                add_to_con(True)
            elif next_num.is_and:
                add_to_con(True)
            elif num>next_num:
                add_to_con(True)
            else:
                add_to_con(False, i)
                
        elif num==100:
            if next_num.is_and:
                add_to_con(True)
            elif next_num.is_point:
                add_to_con(True)
            elif IN(next_num, "ones"):
                add_to_con(True)
            elif IN(next_num, "teens"):
                add_to_con(True)
            elif IN(next_num, "tens"):
                add_to_con(True)
            elif is_multiple1000(next_num):
                add_to_con(True)
            else:
                add_to_con(False, i)
            
    return tuple(bool_container), tuple(idx_container)
    
def _check_mixed_spoken(text: str) -> Tuple[str, List[str, Tuple[int, int], ...]]:
    """ extract mixed numbers like negative 234 point 2 4 three first """
    rreturn = []
    regex_pipes = [
        ORDINAL_NUMERAL_REGEX,
        NUMBER_FOLLOWED_BY_SUFFIX_REGEX,
        MIXED_SPOKEN_REGEX,
        INFORMALS_EXACT_REGEX,
        INFORMALS_MULTIPLYABLE_REGEX,
        #ANY_NUMBER_REGEX,
        #DOT_ANY_NUMBER_REGEX,
    ]
    for _pipe in regex_pipes:
        for match in re.finditer(_pipe,text, re.IGNORECASE | re.UNICODE):
            if len(match.group().split())>1 and _pipe==MIXED_SPOKEN_REGEX:
                lc,rc = count_spaces(match.group())
                start, end = (match.span()[0]+lc
, match.span()[1]-rc
)
                rreturn.append((match.group().strip()
                , (start, end)))
                # we replace the found number with `$` to avoid the next Pipeline extracting the same number again
                text = text_span_replace(text, "$"*(end-start), (start, end))
            elif _pipe!=MIXED_SPOKEN_REGEX:
                lc,rc = count_spaces(match.group())
                start, end = (match.span()[0]+lc
                ,match.span()[1]-rc
                )
                rreturn.append((match.group().strip()
                , (start, end)))
                # we replace the found number with `$` to avoid the next Pipeline extracting the same number again
                text = text_span_replace(text, "$"*(end-start), (start, end))
    return (text, # we pass the text to the next Pipeline
    rreturn)
        

def _normalize_and(numbers: List[List[Union[int, str]]], indexes: List[Tuple[int, int]]) -> List[List[Union[int, str]]]:
    rtidxs1 = []
    def _normalize_and_inner(numbers, indexes):
        rtidxs = []
        for i, (n, _) in enumerate(zip(numbers, indexes)):
            if len(n)>1:
                first = n[0]
                last = n[-1]
                second_last = n[-2]
                if (last in ANDS+POINTS+NEGATIVES):
                    numbers.insert(i+1, [n[-1]])
                    rtidxs.append((indexes[i], "NUMBER"))
                    n.pop(-1)
                elif (second_last in ANDS and last in ZEROS):
                    numbers.insert(i+1, [n[-2]])
                    numbers.insert(i+2, [n[-1]])
                    n.pop(-2); n.pop(-1)
                    rtidxs.append((indexes[i], "NUMBER"))
                elif first in ANDS:
                    numbers.insert(i, [n[0]])
                    n.pop(0)
                    rtidxs.append((indexes[i], "NUMBER"))
                else:
                    rtidxs.append((indexes[i], "NUMBER"))
            elif len(n)==1 and n[0] in ALL_NUMS:
                rtidxs.append((indexes[i], "NUMBER"))
            rtidxs.append(indexes[i])
        return numbers, indexes
    numbers, rtidxs1 = _normalize_and_inner(numbers, indexes)
    return numbers, list(filter(lambda x: isinstance(x, tuple), rtidxs1))

def _recover_real_indices_and_match(text: str, nums: List[List[str]]) -> List[Tuple[str, Tuple[int, int]], ...]:
    last_start = 0
    real = []
    for n in nums:
        ptt = " ".join(n).replace(" ", r"\s{,2}?[,\-]?\s{,2}?")
        ptt = r"\b"+ptt+r"\b"
        for m in re.finditer(ptt, text[last_start:], re.IGNORECASE):
            real.append((m.group(), m.span()))
            last_start=m.span()[0]
            break
    return real

NUMBER_TYPE = "number_type"
NUMBER_VALUE_TYPE = "value_type"
ORDINAL = "ordinal"
FLOAT = "float"
INTEGER = "integer"

def _info_gen(num_string: str, num_val: Union[int, float], spans: Tuple[int, int]) -> Dict[str, Any]:
    data = {}
    data["span"] = spans
    data[NUMBER_TYPE] = "number"
    cleaned = Pipe()(num_string.lower())
    tokens = tokenize(cleaned)
    last = tokens[-1]
    if last in ORDINALS or re.match(ORDINAL_NUMERAL_REGEX, last, re.IGNORECASE):
        data[NUMBER_TYPE] = ORDINAL
    if "point" in tokens or isinstance(num_val, float):
        data[NUMBER_VALUE_TYPE] = FLOAT
    else:
        data[NUMBER_VALUE_TYPE] = INTEGER
    
    return data

@logger.catch
def words2numbers(text: str, debug: bool=False, timeit=False) ->List[Tuple[str, Tuple[int, int]], ...]:
    start_time = perf_counter()
    if debug:
        logger.enable(__name__)
    logger.info("Original text: %s"%text)
    words, mixed_matches = _check_mixed_spoken(text)
    recovery_text = copy(words)
    logger.debug("Text after `first extraction pipe`: %s"%words)
    words = Pipe()(words)
    logger.warning("Normalized for tokenization:  %s:"%words)
    words = tokenize(words)
    logger.debug("Tokenized: %s"%words)
    bools, _ = _check_and_point(words)
    end_idxs =_get_idxs_from_bool(bools)
    nums, idxs =_get_numbers_from_idxs(words, end_idxs)
    norm_nums, _ = _normalize_and(nums, list(map(list, idxs)))
    norm_nums= list(filter(lambda n: (n[0] in ALL_NUMS) or (len(n)>1 and (n[0] in POINTS or n[0] in NEGATIVES)), norm_nums))
    real = _recover_real_indices_and_match(recovery_text, norm_nums)
    real.extend(mixed_matches)
    real = list(map(lambda n: n[0], real))
    rt = []
    for n in real:
        for m in re.finditer(n, text, re.IGNORECASE):
            start, end = m.span()
            rt.append((n, m.span()))
            # we replace the found number with `$` to avoid the next Pipeline extracting the same number again
            text = text_span_replace(text, "$"*(end-start), (start, end))
            break
    last_pipes = [
        NUMBER_FOLLOWED_BY_POWER_REGEX,
        ANY_NUMBER_REGEX,
        DOT_ANY_NUMBER_REGEX,
    ]
    for any_num in last_pipes:
        for m in re.finditer(any_num, text, re.IGNORECASE):
            start, end = m.span()
            rt.append((m.group(), m.span()))
            # we replace the found number with `$` to avoid the next Pipeline extracting the same number again
            text = text_span_replace(text, "$"*(end-start), (start, end))
    end_time = perf_counter()
    rt_final = []
    for n in rt:
        num_string = n[0]
        value = _words2num(num_string)
        rt_final.append((num_string, value, _info_gen(num_string, value, n[1])))
    if debug and not timeit:
        logger.info("Took: %s seconds"%(end_time-start_time))
    if timeit and not debug:
        print("Took: %s seconds"%(end_time-start_time))
    return sorted(rt_final, key=lambda n: n[2]["span"])