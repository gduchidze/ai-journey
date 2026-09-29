import re

text = "Hello, world. This is a test."

result = re.split(r'\s', text)
print(result)

result2 = re.split(r'([,.]|\s)', text)
print(result2)