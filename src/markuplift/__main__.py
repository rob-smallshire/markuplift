"""Entry point for running MarkupLift as a module.

This allows MarkupLift to be executed as:
    python -m markuplift
"""

from .cli import cli

if __name__ == '__main__':
    cli()