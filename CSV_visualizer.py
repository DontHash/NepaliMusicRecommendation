import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns
import numpy as np
from collections import Counter
import re

df = pd.read_csv("./CSVs Dataset/Lyrics_Dataset.csv")
print(df.head())

plt.figure(figsize=(6,4))
sns.countplot(data=df, x='Category', palette='viridis')
plt.title('Number of Songs by Category')
plt.show()


artist_counts = df['Artist'].value_counts().head(20)
plt.figure(figsize=(15,8))
artist_counts.plot(kind='bar', color='skyblue')
plt.title('Top 20 Artists with Most Songs')
plt.ylabel('Number of Songs')
plt.xticks(rotation=75)
plt.show()









