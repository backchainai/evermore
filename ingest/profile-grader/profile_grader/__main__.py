"""Enable `python -m profile_grader ...` alongside the `grade` console script."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
