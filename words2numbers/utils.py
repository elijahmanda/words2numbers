from __future__ import annotations

from typing import Tuple, List,Union, Any, Dict, Callable, Iterable
import random
from random import randint, choice, random as _random_float
from num2words import num2words
from .data import SUFFIXES

def align_results(res: List[Tuple[str, int | float, Dict[str, Union[str, Union[str, Tuple[int, int]]]]]]) -> Tuple[str, float | int, str, Tuple[int, int], str]:
    text = res[0]
    number = res[1]
    info = res[2]
    number_type = info["number_type"]
    span = info["span"]
    value_type = info["value_type"]
    return text, number, number_type, value_type,span
    
def tuple_map(func: Callable[Iterable, Iterable], iterable: Iterable[Iterable[Any, ...]]) -> Tuple[Iterable,...]:
    return tuple(map(func, iterable))

def is_neg_and_ones(num: str | int) -> bool:
    val = parse_num(num)
    if val is None: return False
    if isinstance(val, int) and val<=-1 and val>=-9:
        return True
    return False

def parse_num(num: str) -> int | float | None:
    num = num.lower()
    try:
        val_int = int(num)
    except ValueError:
        val_int = None
    try:
        val_float = float(num)
    except ValueError:
        val_float = None
    if val_float and ("e" in num or "." in num):
        return val_float
    return val_int
    
def text_span_replace(text: str, replacement: str, span: Tuple[int, int]) -> str:
    """ Replace text[span[0] : span[1]] with `replacement` """
    left_chunk = text[0:span[0]]
    right_chunk = text[span[1]:]
    return left_chunk + replacement + right_chunk
    
def get_text_chunks(text: str, span: Tuple[int,int]) -> Tuple[str, str, str]:
    left_chunk = text[0:span[0]]
    right_chunk = text[span[1]:]
    middle_chunk = text[span[0]:span[1]]
    return left_chunk, middle_chunk, right_chunk
    
def pair(tokens: List[Any], last=0) -> List[Tuple[Any, Any]]:
    tk_len = len(tokens)
    if tk_len==1:
        return [(tokens[0], last)]
    if tk_len % 2:
        tokens.append(last)
        tk_len += 1
    new_tokens = []
    n = 0
    while n<=tk_len-1:
        new_tokens.append((tokens[n], tokens[n+1]))
        n += 2
    return new_tokens
    
def gen_nums(
    n: int, # how many numbers
    n_range: int=(int(1e3), int(1e6)),
    points: int=None, # how many points
    negatives: int=None, # how many negatives
    int_nums: int=None, # how many non word integers
    floats: int=None, # how many floating point numbers
    num_suffix:int=None, # how many numbers with suffixes
    ordinal_ints: int= None, # number of ordinal numerals
    shuffle: int=None, # how many times to shuffle the return values
    ) -> List[str, ...]:
    nms = []
    for _ in range(n):
        word = num2words(random.randint(*n_range))
        nms.extend(word.split())
    if points:
        nms.extend(["point" for _ in range(points)])
    if negatives:
        nms.extend(["negative" for _ in range(negatives)])
    if int_nums:
        nms.extend([str(randint(*n_range)) for _ in range(int_nums)])
    if floats:
        fls= _gen_eE_power_numbers(floats)
        nms.extend(fls)
    if num_suffix:
        ns = _gen_suffix_nums(num_suffix)
        nms.extend(ns)
    if ordinal_ints:
        nms.extend(_gen_ordinals(ordinal_ints))
    if shuffle:
        x = shuffle
        while x>0:
            random.shuffle(nms)
            x-=1
    return nms

def random_round(num: Union[float, int]) -> float | int:
    rd = randint(0, 7)
    return round(num, rd)
    

def _gen_eE_power_numbers(n: int) -> List[str]:
    letters = "eE"
    nums = []
    for _ in range(n):
        nums.append(
        str(
            random_round(
                _random_float()*randint(-1000, 1000)))+ \
                choice(letters)+ \
                _gen_sign()+ \
                str(randint(1,99)
                )
            )
    return nums

def _gen_suffix_nums(n: int):
    rt = []
    for _ in range(n):
        num = str(random_round(_random_float()*randint(-1000, 1000)))
        suffix = choice(list(SUFFIXES.keys()))
        suffix = suffix if _random_float()>0.5 else suffix.upper()
        rt.append(num+suffix)
    return rt

def _gen_ordinals(n: int) -> List[str]:
    rt = []
    end_map = {"1": "st", "2": "nd", "3": "rd"}
    for _ in range(n):
        num = str(randint(1, 10000))
        end = num[-1]
        try:
            end_2 = num[-2]
        except IndexError:
            end_2 = None
        if end_2=="1":
            suffix = "th"
        else:
            suffix = end_map.get(end)
            suffix = "th" if not suffix else suffix
        #print("utils:102:_gen_ordinals:->suffix:", suffix)
        #suffix = suffix if _random_float()>0.5 else suffix.upper()
        rt.append(num+suffix)
        #print("utils:102:_gen_ordinals:->num+suffix:", num+suffix)
    return rt

def _gen_sign():
    signs = "+- "
    return choice(signs).strip()

def count_spaces(text: str) -> Tuple[int, int]:
    left = right = 0
    for i in text:
        if i!=" ":
            break
        left+=1
    for i in text[::-1]:
        if i!=" ":
            break
        right+=1
    return (left, right)
    
def verify(text, nums):
    rt = []
    for sp in nums:
        rt.append((text[sp[2]["span"]["start"]:sp[2]["span"]["end"]],sp[1], sp[2]))
    return rt==nums, rt