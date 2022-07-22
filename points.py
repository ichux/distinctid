import random
import re

# pip install matplotlib
import matplotlib.pyplot as plt

hits = []


try:
    for ts in re.findall(r"\d\d+", open("graph_data.txt", "r").read()):
        hits.append(int(ts))

    # plt.suptitle("twitter: @zuoike")
    plt.title("Distinct ID")

    plt.xlabel("Amount of times", fontsize=14)
    plt.ylabel("Requests", fontsize=14)

    plt.plot(hits, color="red")
    plt.savefig("points.png")
except FileNotFoundError:
    print("graph_data.txt is missing")
