from pprint import pprint
from words2numbers.utils import gen_nums, verify
from words2numbers import words2numbers


text = " ".join(gen_nums(5,n_range=(1e3, 1e9), int_nums=5, floats=5, points=5,num_suffix=5,ordinal_ints=5, negatives=5, shuffle=2))
#int_nums=10, floats=10, points=10,num_suffix=10, shuffle=2))+" 6,000 234'424'343 6,907.6183 2.5e-78"
#text = "100 and eighty nine"
#with open("test_data.txt", encoding="utf-8") as f:
#    #text = " ".join(f.read().split())
#    text = f.read()
#text = "234'424'343"
#text = "six hundred and third 5 halves of blablabla"

nums = words2numbers(text, debug=True)
print(len(nums), "Numbers")
pprint(nums)
print("#"*43)
pprint(verify(text, nums))