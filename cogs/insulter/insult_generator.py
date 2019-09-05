"""
Heavily borrowed from https://github.com/ramiabraham/insult-generator/blob/master/plugin.php


We want to generate a random insult from one of four categories, baroque, hook, modern, monty.
Because there are not an equal amount of insults in each of the categories, we should
be a little smart about how we generate these insults. Otherwise, we could generate
the same insults from the smallest categories more often.

We'll accomplish this by weighting each category by the number of nouns they all have.
"""
import random


def get_weight(cat):
    return len(list(open(cat+"/noun.txt")))

def gen_insult(path=""):
    categories = ["baroque", "hook", "modern", "monty"]
    categories = [path+cat for cat in categories]
    weights = [get_weight(cat) for cat in categories]
    # normalize the weights
    weights = [w/sum(weights) for w in weights]

    rand_cat = random.choices(categories, cum_weights=weights)[0]


    adj_one = random.choice(list(open(rand_cat+"/adj_one.txt"))).rstrip()
    adj_two = random.choice(list(open(rand_cat+"/adj_two.txt"))).rstrip()
    noun = random.choice(list(open(rand_cat+"/noun.txt"))).rstrip()

    if random.random() < 0.5:
        insult = "{}, {} {}".format(adj_one, adj_two, noun)
    else:
        if random.random() < 0.5:
            adj = adj_one
        else:
            adj = adj_two
        insult = "{} {}".format(adj, noun)

    return insult
