#! /usr/bin/env python3

# Decompounding as a Service using an HTTP server

import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict
from urllib.parse import parse_qs, urlparse

from decompound import Splitter

logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)


def eprint(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


if len(sys.argv) < 9:
    eprint(
        f"python {sys.argv[0]} dt_candidates word_count_file min_word_count(50) "
        "prefix_length(3) suffix_length(3) word_length(5) dash_word(3) upper(upper) "
        "epsilon port"
    )
    eprint("-----------------------------------------------------")
    eprint("Parameter description:")
    eprint("-----------------------------------------------------")
    eprint(
        "dt_candidates:\t\tfile with words and their split candidates, generated "
        "from a distributional thesaurus (DT)"
    )
    eprint("word_count_file:\tfile with word counts used for filtering")
    eprint(
        "min_word_count:\t\tminimal word count used for split candidates "
        "(recommended paramater: 50)"
    )
    eprint(
        "prefix_length:\t\tlength of prefixes that are appended to the right-sided "
        "word (recommended parameter: 3)"
    )
    eprint(
        "suffix_length:\t\tlength of suffixes that are appended to the left-sided "
        "word (recommended parameter: 3)"
    )
    eprint(
        "word_length:\t\tminimal word length that is used from the split candidates "
        "(recommended parameter: 5)"
    )
    eprint(
        "dash_word:\t\theuristic to split words with dash, which has no big impact "
        "(recommended: 3)"
    )
    eprint(
        "upper:\t\t\tconsider uppercase letters (=upper) or not (=lower). "
        "Should be set for case-sensitive languages e.g. German"
    )
    eprint("epsilon:\t\tsmoothing factor (recommended parameter: 0.01")
    eprint("port: Port the server will run")
    sys.exit(1)


decompounder = Splitter(
    min_word_count=int(sys.argv[3]),
    prefix_length=int(sys.argv[4]),
    suffix_length=int(sys.argv[5]),
    min_word_length=int(sys.argv[6]),
    # 1 -> remove, 2 -> split, 3 -> nothing
    dash_words=Splitter.DashBehaviour(int(sys.argv[7])),
    uppercase_first_letter=True if sys.argv[8] == "upper" else False,
    epsilon=float(sys.argv[9]),
)

port = int(sys.argv[10])

file_knowledge = sys.argv[1]
file_wordcount = sys.argv[2]

decompounder.prepare_decompounding(file_wordcount, file_knowledge)

known_words: Dict[str, str] = {}


class Serv(BaseHTTPRequestHandler):
    def _set_headers(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self) -> None:
        # FIXME: gotta do this
        self._set_headers()
        query_components = parse_qs(urlparse(self.path).query)
        res = []
        for w in query_components["sentence"][0].split():
            if w in known_words:
                res.append(known_words[w])
                continue
            pcand = decompounder.split_compound(w) or w
            res.append(pcand.replace("-", " "))
            known_words[w] = pcand.replace("-", " ")
        self.wfile.write(" ".join(res).encode())


def run(port: int = 80) -> None:
    server_address = ("", port)
    httpd = HTTPServer(server_address, Serv)
    print(f"Starting httpd using port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run(port=port)
