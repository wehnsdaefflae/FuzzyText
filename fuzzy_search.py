import glob
import sys
from os import path
from typing import Tuple, Iterable, Generator

RESULT = Tuple[str, str, int, int, int, float]


def compare(string_a: str, string_b: str) -> float:
    l_a, l_b = len(string_a), len(string_b)
    assert l_a == l_b
    return sum(float(a == b) for a, b in zip(string_a, string_b)) / l_a


def search_file(file_path: str, minimum_similarity: float, search_term: str) -> Generator[RESULT, None, None]:
    l_term = len(search_term)
    context = 10
    with open(file_path, mode="r") as file:
        for l, each_line in enumerate(file):
            each_line = each_line.lower()[:-1]
            l_line = len(each_line)
            for i in range(l_line - l_term):
                found_term = each_line[i:i+l_term]
                s = compare(search_term, found_term)
                if s >= minimum_similarity:
                    r = "..." + each_line[max(0, i-context):min(i + l_term + context, l_line)] + "..."
                    yield r, file_path, -1, l + 1, i, s


def search(file_pattern: str, minimum_similarity: float, search_term: str) -> Iterable[RESULT]:
    for each_file in glob.glob(file_pattern):
        if path.isdir(each_file):
            continue
        yield from search_file(each_file, minimum_similarity, search_term)


def main():
    arguments = sys.argv
    if len(arguments) < 3:
        raise ValueError(f"{arguments[0]} needs two arguments: file pattern, minimum similarity (0. - 1.), and search term in square brackets")

    try:
        similarity = float(arguments[2])

    except ValueError() as e:
        print("The second parameter must be a float number between 0. and 1.")
        raise e

    search_term = " ".join(arguments[3:])
    if not (search_term[0] == "[" and search_term[-1] == "]"):
        raise ValueError("The search term must be enclosed in square brackets.")

    raw_term = search_term[1:-1]
    location = arguments[1]
    print(f"looking for terms in [{arguments[1]}] more similar to [{raw_term}] than {[similarity]}...\n")

    print("result\tfile\tpage\tline\tposition\tsimilarity")
    for result in search(location, similarity, raw_term):
        print(f"{result[0]}\t{result[1]}\t{result[2]}\t{result[3]}\t{result[4]}\t{result[5]}")


if __name__ == "__main__":
    main()
