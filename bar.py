import random
import re

# pip install matplotlib
import matplotlib.pyplot as plt

requests, hits, colors = [], [], []

numbers = re.findall(r"\d\d+", open("graph_data.txt", "r").read())

try:
    for rst, ts in enumerate(numbers, 1):
        requests.append(f"C{str(rst).zfill(2)}")
        hits.append(int(ts))

        colors.append(
            "#{}{}{}{}{}{}".format(
                *(random.choice("0123456789abcdef") for _ in range(6))
            )
        )

    plt.barh(requests, hits, color=colors)

    plt.title("Distinct ID")
    plt.xlabel("Hits per second", fontsize=14)
    plt.ylabel("Requests", fontsize=14)

    plt.savefig("bars.png")
except FileNotFoundError:
    print("graph_data.txt is missing")
