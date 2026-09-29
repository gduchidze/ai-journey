import re

with open("the-verdict.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

preprocessed = re.split(r'([,.:;?_!"()\']|--|\s)', raw_text)
preprocessed = [item.strip() for item in preprocessed if item.strip()]

all_words = sorted(set(preprocessed))
vocab_size = len(all_words)

vocab = {token: integer for integer, token in enumerate(all_words)}


class SimpleTokenizerV1:
    def __init__(self, vocab):
        self.str_to_int = vocab
        self.int_to_str = {i: s for s, i in vocab.items()}

    def encode(self, text):
        preprocessed = re.split(r'([,.:;?_!"()\']|--|\s)', text)

        preprocessed = [
            item.strip() for item in preprocessed if item.strip()
        ]
        ids = [self.str_to_int[s] for s in preprocessed]
        return ids

    def decode(self, ids):
        text = " ".join([self.int_to_str[i] for i in ids])
        # Replace spaces before the specified punctuations
        text = re.sub(r'\s+([,.?!"()\'])', r'\1', text)
        return text


all_tokens = sorted(list(set(preprocessed)))
all_tokens.extend(["<|endoftext|>", "<|unk|>"])

vocab = {token:integer for integer,token in enumerate(all_tokens)}
# for i, item in enumerate(list(vocab.items())[-5:]):
#     print(item)


class SimpleTokenizerV2:
    def __init__(self, vocab):
        self.str_to_int = vocab
        self.int_to_str = {i: s for s, i in vocab.items()}

    def encode(self, text):
        preprocessed = re.split(r'([,.:;?_!"()\']|--|\s)', text)
        preprocessed = [item.strip() for item in preprocessed if item.strip()]
        preprocessed = [
            item if item in self.str_to_int
            else "<|unk|>" for item in preprocessed
        ]

        ids = [self.str_to_int[s] for s in preprocessed]
        return ids

    def decode(self, ids):
        text = " ".join([self.int_to_str[i] for i in ids])
        # Replace spaces before the specified punctuations
        text = re.sub(r'\s+([,.:;?!"()\'])', r'\1', text)
        return text

tokenizer = SimpleTokenizerV2(vocab)

text1 = "Hello, do you like tea?"
text2 = "In the sunlit terraces of the palace."

text = " <|endoftext|> ".join((text1, text2))

print(text)

print(tokenizer.encode(text))
print(tokenizer.decode(tokenizer.encode(text)))

# **Notes (3 sentences):**
#
# A tokenizer turns text into integer IDs
# (`encode`, via `str_to_int`) and
# back into text (`decode`, via the flipped `int_to_str`),
# because language models only work with numbers.
# V1 crashes with `KeyError` on any word missing from `vocab`,
# while V2 adds `<|unk|>` and `<|endoftext|>`,
# replaces unknown words before lookup (so `pizza` and
# `sushi` both become `<|unk|>` and information is lost),
# and fixes the decode regex to also handle `:` and `;`.
# `decode` works in two steps, where `" ".join`
# blindly adds a space between every token (`Hi , you ?`) and
# `re.sub` removes the spaces before punctuation (`Hi, you?`), and
# the next improvement is subword tokenization (BPE),
# which splits unknown words into known pieces
# like `un + happy + ness`.