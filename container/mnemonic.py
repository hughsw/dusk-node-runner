
from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39Languages,
    Bip39WordsNum,
    Bip39MnemonicValidator,
)

# Generate a random mnemonic string of 12 words with default language (English)
# A Mnemonic object will be returned
mnemonic = Bip39MnemonicGenerator(Bip39Languages.ENGLISH).FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)

# Get words count
print(mnemonic.WordsCount())
# Get as string
print(mnemonic.ToStr())
# str
print(f'{mnemonic}')
# Get as list of strings
print(mnemonic.ToList())

is_valid = Bip39MnemonicValidator(Bip39Languages.ENGLISH).IsValid(mnemonic)

assert is_valid, str((mnemonic,))
