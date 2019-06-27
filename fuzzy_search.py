# coding=utf-8
import time
import glob
import sys
from os import path
from typing import Tuple, Iterable, Generator, Optional, Sequence


class Timer:
    _last_time = -1  # type: int

    @staticmethod
    def time_passed(passed_time_ms: int) -> bool:
        if 0 >= passed_time_ms:
            raise ValueError("Only positive millisecond values allowed.")

        this_time = round(time.time() * 1000.)

        if Timer._last_time < 0:
            Timer._last_time = this_time
            return False

        elif this_time - Timer._last_time < passed_time_ms:
            return False

        Timer._last_time = this_time
        return True


RESULT = Tuple[str, str, int, int, float]


def compare(string_a: str, string_b: str) -> float:
    l_a, l_b = len(string_a), len(string_b)
    assert l_a == l_b
    return sum(float(a == b) for a, b in zip(string_a, string_b)) / l_a


def yield_characters(file_path: str) -> Generator[Tuple[str, int, int], None, None]:
    size = path.getsize(file_path)
    progress = 0
    with open(file_path, mode="r") as file:
        for l, each_line in enumerate(file):
            for i, c in enumerate(each_line):
                yield c, l + 1, i

            progress += len(each_line)
            if Timer.time_passed(2000):
                print(f"finished {100. * progress / size:5.2f}% of reading {file_path}...")


def yield_window(
        character_generator: Generator[Tuple[str, int, int], None, None],
        size: int,
        skip_list: Optional[Sequence[str]] = None,
        lower_case: bool = False) -> Generator[Sequence[Tuple[str, int, int]], None, None]:

    window = [next(character_generator) for _ in range(size - 1)]

    for c, l, i in character_generator:
        if c in skip_list:
            continue
        if lower_case:
            c = c.lower()
        position = c, l, i
        window.append(position)
        yield window
        del(window[0])


def stringify(window: Sequence[Tuple[str, int, int]], start: int = 0, end: int = -1) -> str:
    return "".join(_c for _c, _, _ in window[start:end])


def search_file(file_path: str, minimum_similarity: float, search_term: str, context: int = 5) -> Generator[RESULT, None, None]:
    print(f"searching for [{search_term}] in [{file_path}]...")
    l_term = len(search_term)
    character_generator = yield_characters(file_path)
    window_generator = yield_window(character_generator, context + l_term + context, skip_list=["\n"], lower_case=True)

    window = next(window_generator)
    for _i in range(context):
        each_term = stringify(window, _i, _i + l_term)
        s = compare(search_term, each_term)
        if s >= minimum_similarity:
            prefix = " " * (context - _i) + stringify(window, 0, _i)
            postfix = stringify(window, context + l_term, context + l_term + context)
            yield "..." + prefix + each_term.upper() + postfix + "...", file_path, window[_i][1], window[_i][2], s

    for window in window_generator:
        each_term = stringify(window, context, context + l_term)
        s = compare(search_term, each_term)
        if s >= minimum_similarity:
            prefix = stringify(window, 0, context)
            postfix = stringify(window, context + l_term, context + l_term + context)
            yield "..." + prefix + "[" + each_term.upper() + "]" + postfix + "...", file_path, window[context][1], window[context][2], s


def search(file_pattern: str, minimum_similarity: float, search_term: str) -> Iterable[RESULT]:
    file_list = glob.glob(file_pattern)
    l_list = len(file_list)
    for _i, each_file in enumerate(file_list):
        if not path.isfile(each_file):
            continue
        print(f"starting file {_i + 1} of {l_list}...")
        yield from search_file(each_file, minimum_similarity, search_term)


def main():
    arguments = sys.argv
    l_arguments = len(arguments)
    print()

    if l_arguments == 1:
        print("DEBUG PARAMETERS")
        arguments.append("data\\big.txt")
        arguments.append(".8")
        arguments.append("results.csv")
        arguments.append("[fathom ]")

    elif l_arguments < 4:
        raise ValueError(f"\n{arguments[0]} needs four arguments: file pattern, minimum similarity (0. - 1.), target result file, and search term in square brackets"
                         f'\ne.g. "python {arguments[0]} data\\big.txt .8 results.csv [fathom ]"'
                         f"\navoid spaces in path names!"
                         )

    try:
        similarity = float(arguments[2])

    except ValueError() as e:
        print("The second parameter must be a float number between 0. and 1.")
        raise e

    result_path = arguments[3]

    search_term = " ".join(arguments[4:])
    if not (search_term[0] == "[" and search_term[-1] == "]"):
        raise ValueError("The search term must be enclosed in square brackets.")

    raw_term = search_term[1:-1]
    location = arguments[1]
    print(f"storing terms from [{location}] that are more similar to [{raw_term}] than [{100.*similarity:5.2f}%] to [{result_path}]...\n")

    with open(result_path, mode="w") as file:
        header = "result\tfile\tline\tposition\tsimilarity\n"
        file.write(header)
        for result in search(location, similarity, raw_term):
            line = f"{result[0]}\t{result[1]}\t{result[2]:d}\t{result[3]:d}\t{100. * result[4]:05.2f}\n"
            file.write(line)


if __name__ == "__main__":
    main()
