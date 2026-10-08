import argparse

from agent import handle


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the support agent on one ticket.")
    ap.add_argument("ticket")
    print(handle(ap.parse_args().ticket))


if __name__ == "__main__":
    main()
