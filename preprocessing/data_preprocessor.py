import pandas as pd
import string
import re
import os
import itertools
from tqdm import tqdm


def get_olid_data():
    file_path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(file_path, "../data/olid-training-v1.0.tsv"), sep="\t", header=0)


def remove_amp(tweets):
    for i in range(len(tweets)):
        tweets[i] = tweets[i].replace("&amp", "").replace("&amp;", "")
    return tweets


def process_hashtag_punctuation(hashtag):
    for char in string.punctuation:
        if char == "#":
            hashtag = hashtag.replace(char, "HASHTAG")
        elif char == "'":
            hashtag = hashtag.replace(char, "")
        else:
            hashtag = hashtag.replace(char, " " + char + " ")
    return hashtag


def replace_underscore(word_list):
    new_word_list = []
    for word in word_list:
        word_parts = word.split("_")
        for part in word_parts:
            new_word_list.append(part)
    return new_word_list


def split_word(hashtag):
    post_process_parts = []
    current_chars = []
    for char in hashtag:
        if len(current_chars) == 0:
            current_chars.append(char)
        else:
            last_char = current_chars[-1]

            # if last character is upper case
            if last_char.isupper():
                if char.isupper() or (len(current_chars) == 1 and char.islower()):
                    current_chars.append(char)
                else:
                    post_process_parts.append("".join(current_chars))
                    current_chars = [char]

            elif last_char.islower():
                if char.islower():
                    current_chars.append(char)
                else:
                    post_process_parts.append("".join(current_chars))
                    current_chars = [char]

            elif last_char.isdigit():
                if char.isdigit():
                    current_chars.append(char)
                else:
                    post_process_parts.append("".join(current_chars))
                    current_chars = [char]
            else:
                if char in string.punctuation:
                    current_chars.append(char)
                elif char == " ":
                    continue
                else:
                    post_process_parts.append("".join(current_chars))
                    current_chars = [char]
    # Make sure to append the last part
    post_process_parts.append("".join(current_chars))
    return post_process_parts


def common_words():
    file_path = os.path.dirname(__file__)
    words = [word.strip("\n") for word in open(file_path + "../data/google-10000-english-usa.txt")]
    for word in words:
        if len(word) == 2 and word[0] not in "aeiou" and word[1] not in "aeiou" and word != "st":
            words.remove(word)

    return set(words)


def match_word_to_dic(word, level):
    if level > 6:
        return word

    # if entire word not in dictionary words
    if word not in dict_words:
        # get all substrings in word
        matched_words = []
        for dict_word in dict_words:
            if dict_word in word:
                matched_words.append(dict_word)
        # Max out at 30 matches
        matched_words = sorted(matched_words, key=len, reverse=True)[:30]

        # Get best match by maxing match length over string
        best_match = ""
        best_match_parts = []
        best_match_av_token_length = 0
        for i in range(1, 11):
            for combination in itertools.combinations(matched_words, i):
                seq = "".join(combination)
                if seq in word and len(seq) >= len(best_match) and len(seq) / len(
                        combination) > best_match_av_token_length:
                    # Check to make sure combination starts or ends string
                    if word.startswith(seq) or word.endswith(seq):
                        best_match = seq
                        best_match_parts = combination
                        best_match_av_token_length = len(seq) / len(combination)

        # Once you get best match, get part of word that doesn't contain best match
        left_over = word.replace(best_match, "")
        best_match_parts = list(best_match_parts)
        if left_over != "":
            if best_match + left_over == word:
                best_match_parts.append(left_over)
            else:
                best_match_parts.insert(0, left_over)

        for i in range(len(best_match_parts)):
            if best_match_parts[i] not in dict_words:
                best_match_parts[i] = match_word_to_dic(best_match_parts[i], level + 1)

        word = " ".join(best_match_parts)

    return word


dict_words = common_words()


def find_words_in_contiguous_string(words):
    terms_to_ignore = ["SCOTUS", "USA", "MAGA", "POTUS", "TCOT", "HASHTAG ", "HASHTAG", "ANTIFA", "DEM", "GOP", "BBUK", "NHS", "TRUMP"]
    output = []
    for word in words:
        # Only all lower or all upper
        if ((word.islower() or word.isupper()) and (word not in terms_to_ignore and word.upper() not in terms_to_ignore)) \
                or len(word) >= 15: # 15 is long
            word = word.lower()

            word = match_word_to_dic(word, 0)
        # append word to output
        output.append(word)
    return output


def process_hastags(tweet):
    post_processing_parts = []
    # split by whitespace and check for
    words = tweet.split(" ")
    for word in words:
        # If word is a hashtag, split by upper case letter or number
        if "#" in word:
            old_word = word
            # Deal with punctuation
            word = process_hashtag_punctuation(word)
            # Regex to find words and also split hashtag by underscores
            words = replace_underscore([a for a in re.split('([A-Z][a-z]+)', word) if a])
            # Split words that have distinct parts (i.e. words and numbers) into their distinct parts
            post_split = []
            for word in words:
                word_split = split_word(word)
                for part in word_split:
                    post_split.append(part)
            words = post_split

            # Finally, find words in word
            word = " ".join(find_words_in_contiguous_string(words))
            # print(old_word, "------->", " ".join(split_word(word)))
        post_processing_parts.append(word)
    return " ".join(post_processing_parts)


if __name__ == "__main__":
    tweets = get_olid_data()["tweet"]
    for tweet in tqdm(list(remove_amp(tweets))):
        print(process_hastags(tweet))
