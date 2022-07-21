import random

# pip install matplotlib
import matplotlib.pyplot as plot

requests, hits, color = [], [], []


for rst, ts in enumerate([_ for _ in open("graph_data.txt", "r").readlines()], 1):
    requests.append(f"C{str(rst).zfill(2)}")
    hits.append(int(ts.strip()))

    color.append(
        "#{}{}{}{}{}{}".format(*(random.choice("0123456789abcdef") for _ in range(6)))
    )


plot.barh(requests, hits, color=color)

plot.title("Distinct ID")
plot.xlabel("Hits per second", fontsize=14)
plot.ylabel("Requests", fontsize=14)

plot.savefig("requests.png")
