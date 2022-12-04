from __future__ import annotations

import re
from typing import Union, List, Tuple
from .normalize import Pipe
from .utils import pair
from .ejtoken import tokenize 
from .data import (
    ALL_NUMS,
    ONES,
    TENS,
    MULTIPLES,
    INFORMAL_ALL,
    SUFFIXES,
    NEGATIVES,
    ORDINAL_SUFFIXES,
    ORDINAL_NUMERAL_REGEX,
)

# logging
from loguru import logger

logger.disable(__name__)

@logger.catch
def _convert_int_or_float(tokens: List[Union[str, float, int]]) -> List[Union[str, int, float]]:
    def _inner_conv(n):
        try:
            if isinstance(n, str):
                if "." in n:
                    raise ValueError
            return int(n)
        except ValueError:
            try:
                return float(n)
            except ValueError:
                return n
    tokens_ = [_inner_conv(token) for token in tokens]
    return tokens_
    
@logger.catch
def _word_to_number(tokens: List[Union[str, float, int]]) -> List[Union[str, int, float]]:
    def _inner_conv(word):
        val = ALL_NUMS.get(word)
        if val:
            return val
        return word
    return [_inner_conv(token) for token in tokens]

def _convert_nums_with_suffix(tokens: List[Union[str, float, int]]) -> List[Union[str, int, float]]:
    def _inner_conv(n):
        if not isinstance(n, str):
            return n
        n = n.lower()
        num = n[:-1]
        suffix = n[-1]
        logger.warning("num: %s; suffix: %s"%(num, suffix))
        if not suffix in SUFFIXES:
            return n
        num = _convert_int_or_float([num])[0]
        if isinstance(num, str):
            return n
        multiply = SUFFIXES[suffix]
        return num * multiply

        
    return [_inner_conv(token) for token in tokens]
    
def _convert_num_ordinals(tokens: List[Union[str, int, float]]) -> List[Union[str, int, float]]:
    def _inner_conv(n):
        if isinstance(n, str):
            if re.match(ORDINAL_NUMERAL_REGEX,n):
                n = int(n[:-2])
        return n
    return [_inner_conv(token) for token in tokens]
    

class _ConversionPipe:
    def __init__(self):
        self._pipes = [
            lambda tokens: [re.sub(r"[',]", "", token) for token in tokens],
            lambda tokens: [token for token in tokens if token!="and"],
            _convert_num_ordinals,
            _convert_int_or_float,
            _word_to_number,
            _convert_nums_with_suffix,
        ]
    
    @logger.catch
    def __call__(self, tokens: List[Union[str, int, float]]) -> List[Union[int, float, str]]:
        for pipe in self._pipes:
            tokens = pipe(tokens)
        return tokens


def _pair_tokens(tokens: List[int]) -> List[List[int, ...]]:
    logger.warning("Tokens recieved before final: %s"%tokens)
    build = []
    final = []
    for token in tokens:
        if token<=100:
            logger.warning("token<=100: %s"%token)
            build.append(token)
            logger.warning("After token<=100: %s; build => %s"%(token, build))
        else:
            logger.warning("build and final after token(%s)>100; build=> %s; final=> %s"%(token, build, final))
            final.append(build)
            logger.warning("")
            build = []
            logger.warning("final after build.clear()=> %s"%(final))
            logger.warning("final after final.append(build)=> %s"%(final))
            final.append([token])
            logger.warning("final after final.append([token])=> %s"%(final))
    final.append(build)
    logger.warning("final %s"%final)
    return final

def _sum_nums(tokens: List[List[int]]) -> int:
    logger.warning("Tokens recieved in _sum_nums: %s"%tokens)
    total = []
    hundred = 0
    for token in tokens:
        if len(token)==1 and not token[0]%1000:
            total.append(token[0])
        else:
            hundred = 0
            for j, n in enumerate(token):
                if j==0:
                    hundred+=n
                    continue
                if n==100:
                    hundred*=100
                    continue
                else:
                    hundred+=n
            total.append(hundred)
    return total

def _find_total(tokens: List[Tuple[int, int]]):
    logger.warning("Tokens recieved in _find_total: %s"%tokens)
    total = 0
    for n in tokens:
        num, multiplier = n
        if not num:
            total+=multiplier
        elif not multiplier:
            total+=num
        else:
            total+=num*multiplier
    return total

# some utility function
def _ensure_iterable(obj):
    if hasattr(obj, "__iter__"):
        return [str(i) for i in obj]
    return [str(obj),]

def _words2num(text: str) -> Union[int, float]:
    cleaned = Pipe()(text.lower())
    tokens = tokenize(cleaned)
    tokens = _ConversionPipe()(tokens)
    points = None
    negative = False
    if tokens[0] in NEGATIVES:
        tokens.pop(0)
        negative = True
    if "point" in tokens:
        point_idx = tokens.index("point")
        points = "".join(_ensure_iterable(tokens[point_idx+1:]))
        points = "0."+points
        tokens = tokens[:point_idx]
        
    paired = _pair_tokens(tokens)
    logger.warning("paired %s"%paired)
    summed = _sum_nums(paired)
    logger.warning("Summed: %s"%summed)
    new_tokens = []
    for token in summed:
        if isinstance(token, (list, tuple)):
            new_tokens.append(token[0])
        else:
            new_tokens.append(token)
    total = _find_total(pair(new_tokens))
    logger.warning("points: %s"%points)
    if points:
        total+=float(points)
    if negative:
        total*=-1
    if int(total)==total and total<1e15:
        total = int(total)
    return total