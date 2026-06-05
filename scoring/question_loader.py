import pandas as pd

def load_questions():

    df = pd.read_csv("questions.csv")

    return df