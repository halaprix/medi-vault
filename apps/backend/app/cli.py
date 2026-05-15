"""CLI utilities for medi-vault."""

import click

from app.core.security import generate_key


@click.group()
def cli():
    """medi-vault management commands."""
    pass


@cli.command()
def generate_key_cmd():
    """Generate a new Fernet encryption key for ENCRYPTION_KEY."""
    key = generate_key()
    click.echo(f"ENCRYPTION_KEY={key}")
    click.echo("")
    click.echo("Add this to your .env file or export it as an environment variable.")


if __name__ == "__main__":
    cli()
