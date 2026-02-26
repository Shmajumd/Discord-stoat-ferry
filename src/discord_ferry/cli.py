"""CLI entry point for Discord Ferry (power users / Linux)."""

import click


@click.group(invoke_without_command=True)
@click.argument("export_dir", type=click.Path(exists=True))
@click.option("--stoat-url", envvar="STOAT_URL", help="Stoat API base URL")
@click.option("--token", envvar="STOAT_TOKEN", help="Stoat user/bot token")
@click.option("--server-id", default=None, help="Use existing Stoat server")
@click.option("--server-name", default=None, help="Name for new server")
@click.option("--skip-messages", is_flag=True, help="Structure only")
@click.option("--skip-emoji", is_flag=True, help="Skip emoji upload")
@click.option("--skip-reactions", is_flag=True, help="Skip reactions")
@click.option("--skip-threads", is_flag=True, help="Skip threads/forums")
@click.option("--rate-limit", default=1.0, type=float, help="Seconds between messages")
@click.option("--upload-delay", default=0.5, type=float, help="Seconds between uploads")
@click.option("--output-dir", default="./ferry-output", help="Report output directory")
@click.option("--resume", is_flag=True, help="Resume from state file")
@click.option("--verbose", "-v", is_flag=True, help="Debug output")
@click.pass_context
def main(ctx: click.Context, /, **kwargs: object) -> None:
    """Migrate a Discord server export to Stoat."""
    # TODO: implement
    raise NotImplementedError


@main.command()
@click.argument("export_dir", type=click.Path(exists=True))
def validate(export_dir: str) -> None:
    """Parse and validate export only, no API calls."""
    # TODO: implement
    raise NotImplementedError


if __name__ == "__main__":
    main()
