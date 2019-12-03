import sys
import collections

URL_LOG = "tests/urllog.txt"

collected = collections.defaultdict(collections.Counter)

with open(URL_LOG) as fh:
    requests = 0
    for line in fh:
        requests += 1
        (user, url) = line.rstrip().split("\t")
        collected[url][user] += 1

    urls = len(collected)
    usersPerUrl = sum(len(x) for x in collected.values()) / urls
    requestsPerUrl = requests / urls


msg = f"""{"REQUESTS":>10} {"URLS":>10} {"USERS/URL":>10} {"REQ/URL":>10}
{requests:>10d} {urls:>10d} {usersPerUrl:>10.01f} {requestsPerUrl:>10.01f}
"""

sys.stdout.write(msg)
sys.stderr.write(msg)
