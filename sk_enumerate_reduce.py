import argparse
import csv
import time
from pathlib import Path

import sk_core as sk


def run_enumeration(n, max_steps, output_path):
    combinators = ["S", "K"]
    bin_mapping = {"S": "10", "K": "11"}
    app_marker = "'"
    app_bin = "0"

    terms = sk.enumerate_terms(n, combinators, bin_mapping, app_marker, app_bin)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for item in terms:
        human_term = item["human"]
        final_tree, steps, normalized = sk.evaluate_combinator(item["tree"], sk.COMBINATORS, max_steps)

        if normalized:
            normal_form = sk.tree_to_human_str(final_tree)
            normal_form_size = sk.count_leaves(final_tree)
            steps_value = steps
            unresolved = False
        else:
            normal_form = "N/A"
            normal_form_size = None
            steps_value = "N/A"
            unresolved = True

        rows.append(
            {
                "Human-Readable Term": human_term,
                "Reduction Steps": steps_value,
                "Normal Form": normal_form,
                "Normal Form Size": normal_form_size,
                "_unresolved": unresolved,
            }
        )

    rows.sort(key=lambda row: (not row["_unresolved"], -(row["Normal Form Size"] or 0)))

    with output_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "Human-Readable Term",
                "Reduction Steps",
                "Normal Form",
                "Normal Form Size",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "Human-Readable Term": row["Human-Readable Term"],
                    "Reduction Steps": row["Reduction Steps"],
                    "Normal Form": row["Normal Form"],
                    "Normal Form Size": row["Normal Form Size"] if row["Normal Form Size"] is not None else "N/A",
                }
            )

    return len(terms)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Enumerate S,K combinator terms and perform bounded normal-order reduction."
    )
    parser.add_argument(
        "-n",
        "--term-length",
        type=int,
        default=7,
        help="Length of the combinator terms to enumerate (number of leaves).",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=15,
        help="Maximum number of normal-order reduction steps per term.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="SK_enumeration_N{n}.csv",
        help="Output CSV path. Use '{n}' to interpolate the term length.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_path = args.output.format(n=args.term_length)

    print(f"Enumerating all S/K terms of length {args.term_length}...")
    start = time.time()
    count = run_enumeration(args.term_length, args.max_steps, output_path)
    elapsed = time.time() - start
    print(
        f"Wrote {count} rows to {output_path} in {elapsed:.2f} seconds."
    )
