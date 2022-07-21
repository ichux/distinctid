import random
import re

# pip install matplotlib
import matplotlib.pyplot as plot

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

    plot.barh(requests, hits, color=colors)

    plot.title("Distinct ID")
    plot.xlabel("Hits per second", fontsize=14)
    plot.ylabel("Requests", fontsize=14)

    plot.savefig("requests.png")
except FileNotFoundError:
    print("graph_data.txt is missing")
