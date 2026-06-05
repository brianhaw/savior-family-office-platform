import pandas as pd


def load_questions():
    df = pd.read_csv("data/questions.csv")
    return df