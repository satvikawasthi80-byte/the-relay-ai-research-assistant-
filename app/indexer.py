from .retrieval import get_retriever


def main():
    print("Starting paper indexing...")

    try:
        retriever = get_retriever()

        total_passages = len(retriever.passages)
        total_papers = len({
            passage["paper"]
            for passage in retriever.passages
        })

        print("\nIndexing completed successfully!")
        print(f"Total papers indexed: {total_papers}")
        print(f"Total passages indexed: {total_passages}")

        print("\nIndexed papers:")

        for paper in sorted({
            passage["paper"]
            for passage in retriever.passages
        }):
            print(f"- {paper}")

    except Exception as error:
        print("\nIndexing failed!")
        print(f"Error: {error}")


if __name__ == "__main__":
    main()