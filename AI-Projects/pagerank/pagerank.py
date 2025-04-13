import os
import random
import re
import sys

DAMPING = 0.85
SAMPLES = 10000


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python pagerank.py corpus")
    corpus = crawl(sys.argv[1])
    ranks = sample_pagerank(corpus, DAMPING, SAMPLES)
    print(f"PageRank Results from Sampling (n = {SAMPLES})")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")
    ranks = iterate_pagerank(corpus, DAMPING)
    print(f"PageRank Results from Iteration")
    for page in sorted(ranks):
        print(f"  {page}: {ranks[page]:.4f}")


def crawl(directory):
    """
    Parse a directory of HTML pages and check for links to other pages.
    Return a dictionary where each key is a page, and values are
    a set of all other pages in the corpus that are linked to by the page.
    """
    pages = {}

    for filename in os.listdir(directory):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(directory, filename)) as f:
            contents = f.read()
            links = re.findall(r'<a\s+(?:[^>]*?)href="([^\"]*)"', contents)
            pages[filename] = set(links) - {filename}

    # Only include links to other pages in the corpus
    for filename in pages:
        pages[filename] = set(link for link in pages[filename] if link in pages)

    return pages


def transition_model(corpus, page, damping_factor):
    """
    Return a probability distribution over which page to visit next,
    given a current page.

    With probability `damping_factor`, choose a link at random
    linked to by `page`. With probability `1 - damping_factor`, choose
    a link at random chosen from all pages in the corpus.
    """
    num_pages = len(corpus)
    probabilities = {}

    if corpus[page]:  # If the page has outgoing links
        for linked_page in corpus:
            probabilities[linked_page] = (1 - damping_factor) / num_pages
        for linked_page in corpus[page]:
            probabilities[linked_page] += damping_factor / len(corpus[page])
    else:  # If the page has no outgoing links, distribute equally
        for linked_page in corpus:
            probabilities[linked_page] = 1 / num_pages

    return probabilities


def sample_pagerank(corpus, damping_factor, n):
    """
    Return PageRank values for each page by sampling `n` pages
    according to the transition model, starting with a random page.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1).
    """
    page_rank = {page: 0 for page in corpus}
    page = random.choice(list(corpus.keys()))  # Start with a random page

    for _ in range(n):
        page_rank[page] += 1
        probabilities = transition_model(corpus, page, damping_factor)
        page = random.choices(list(probabilities.keys()), weights=probabilities.values())[0]

    # Normalize values so they sum to 1
    total = sum(page_rank.values())
    page_rank = {page: rank / total for page, rank in page_rank.items()}

    return page_rank


def iterate_pagerank(corpus, damping_factor, convergence_threshold=0.001):
    """
    Return PageRank values for each page by iteratively updating
    PageRank values until values converge.

    Return a dictionary where keys are page names, and values are
    their estimated PageRank value (a value between 0 and 1).
    """
    num_pages = len(corpus)
    page_rank = {page: 1 / num_pages for page in corpus}

    converged = False
    while not converged:
        new_rank = {}
        converged = True  # Assume convergence unless proven otherwise

        for page in corpus:
            total = 0
            for link in corpus:
                if page in corpus[link]:  # If the page is linked to
                    total += page_rank[link] / len(corpus[link])
                if not corpus[link]:  # If a page has no links, treat it as linking to all pages
                    total += page_rank[link] / num_pages

            new_rank[page] = (1 - damping_factor) / num_pages + damping_factor * total

            # Check for convergence
            if abs(new_rank[page] - page_rank[page]) > convergence_threshold:
                converged = False

        page_rank = new_rank

    return page_rank


if __name__ == "__main__":
    main()
