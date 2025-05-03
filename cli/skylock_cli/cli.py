"""
This module contains commands the user can run to interact with the SkyLock.
"""

from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
import typer
import re
from rich.console import Console
from rich.table import Table
from art import text2art
from skylock_cli.core import (
    auth,
    dir_operations,
    file_operations,
    nav,
    path_parser,
    url_manager,
)
from skylock_cli.model.privacy import Privacy

app = typer.Typer(pretty_exceptions_show_locals=False)
console = Console()


@app.command()
def register(
    username: Annotated[str, typer.Argument(help="The username of the new user")],
) -> None:
    """
    Register a new user in the SkyLock
    """
    email = typer.prompt("Email")

    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.fullmatch(email_regex, email):
        typer.secho(
            "Invalid email address. Please enter a valid email.", fg=typer.colors.RED
        )
        raise typer.Exit(code=1)
    password = typer.prompt("Password", hide_input=True)
    confirm_password = typer.prompt("Confirm password", hide_input=True)
    if password != confirm_password:
        typer.secho("Passwords do not match. Please try again.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    auth.register_user(username, password, email)
    typer.secho("Check you mailbox for the 2FA code")
    code = typer.prompt("Enter 2FA code")
    auth.verify_code(username, password, code, email)
    typer.secho("User registered successfully", fg=typer.colors.GREEN)


@app.command()
def login(
    username: Annotated[str, typer.Argument(help="The username of the user")],
) -> None:
    """
    Login to the SkyLock as a user
    """
    password = typer.prompt("Password", hide_input=True)
    context = auth.login_user(username, password)

    typer.secho("User logged in successfully", fg=typer.colors.GREEN)
    typer.secho("Hello, " + username, fg=typer.colors.GREEN)
    typer.secho("Welcome to our file hosting service", fg=typer.colors.BLUE, bold=True)
    typer.secho(text2art("SkyLock"), fg=typer.colors.BLUE)
    typer.secho(
        f"Your current working directory is: {context.cwd.path}",
        fg=typer.colors.BLUE,
    )


@app.command()
def mkdir(
    directory_path: Annotated[
        Path, typer.Argument(help="The path of the new directory")
    ],
    parent: Annotated[
        Optional[bool],
        typer.Option("--parent", help="Create parent directories as needed"),
    ] = False,
    privacy: Annotated[
        Optional[Privacy],
        typer.Option(
            "--mode", help="Visibility mode: 'protected', 'public', or 'private'"
        ),
    ] = Privacy.PRIVATE,
) -> None:
    """
    Create a new directory in the SkyLock
    """
    new_dir = dir_operations.create_directory(directory_path, parent, privacy)
    pwd()
    typer.secho(
        f"Directory {new_dir.path} created successfully",
        fg=typer.colors.GREEN,
    )
    typer.secho(
        f"Visibility: {new_dir.visibility_label}",
        fg=new_dir.visibility_color,
    )


@app.command()
def rmdir(
    directory_path: Annotated[
        str,
        typer.Argument(
            help="Path to the directory to be removed. Must end with / as this command removes directories, not files.",
        ),
    ],
    recursive: Annotated[
        Optional[bool],
        typer.Option(
            "-r",
            "--recursive",
            help="Remove directories and their contents recursively",
        ),
    ] = False,
) -> None:
    """
    Remove a directory from the SkyLock.
    """
    removed_path = dir_operations.remove_directory(directory_path, recursive)
    pwd()
    typer.secho(f"Directory {removed_path} removed successfully", fg=typer.colors.GREEN)


@app.command()
def rm(
    file_path: Annotated[
        str,
        typer.Argument(
            help="The path of the file to remove. Must not end with / as this command removes files, not directories."
        ),
    ],
) -> None:
    """
    Remove a file from the SkyLock.
    """
    removed_path = file_operations.remove_file(file_path)
    pwd()
    typer.secho(f"File {removed_path} removed successfully", fg=typer.colors.GREEN)


@app.command()
def ls(
    directory_path: Annotated[
        Optional[Path], typer.Argument(help="The directory to list")
    ] = Path("."),
    long: Annotated[
        bool, typer.Option("-l", "--long", help="List in long format")
    ] = False,
) -> None:
    """
    List the contents of a directory.
    """
    contents, path = nav.list_directory(directory_path)

    typer.secho(f"Contents of {path}", fg=typer.colors.BLUE)

    if long and contents:
        table = Table()
        table.add_column("Type", justify="left")
        table.add_column("Name", justify="left", no_wrap=True)
        table.add_column("Path", justify="left")
        table.add_column("Visibility", justify="left")

        for item in contents:
            table.add_row(
                f"[{item.color}]{item.type_label}[/{item.color}]",
                f"[{item.color}]{item.name}[/{item.color}]",
                f"[{item.color}]{item.path}[/{item.color}]",
                f"[{item.visibility_color}]{item.visibility_label}[/{item.visibility_color}]",
            )

        console.print(table)
    else:
        for item in contents:
            typer.echo(typer.style(f"{item.name}", fg=item.color), nl=False)
            typer.echo("  ", nl=False)

    if contents:
        typer.echo()
    else:
        typer.secho("No contents in directory", fg=typer.colors.YELLOW)


@app.command()
def cd(
    directory_path: Annotated[Path, typer.Argument(help="The directory to change to")],
) -> None:
    """
    Change the current working directory.
    """
    new_cwd = nav.change_directory(directory_path)
    typer.secho(f"Changed directory to {new_cwd}", fg=typer.colors.GREEN)


@app.command()
def pwd() -> None:
    """
    Print the current working directory.
    """
    cwd = nav.get_working_directory()
    typer.secho(f"Current working directory: {cwd.path}", fg=typer.colors.BLUE)


@app.command()
def upload(
    file_path: Annotated[Path, typer.Argument(help="The path of the file to upload")],
    destination_path: Annotated[
        Path,
        typer.Argument(
            help="The destination path to upload the file to. Defaults to the current directory.",
        ),
    ] = Path("."),
    force: Annotated[
        Optional[bool], typer.Option("-f", "--force", help="Overwrite existing file")
    ] = False,
    # Commented out for now as we don't let user define privacy in upload
    # privacy: Annotated[
    #     Privacy, typer.Option(
    #         "--mode", help="Visibility mode: 'protected', 'public', or 'private'"
    #     )
    # ] = Privacy.PRIVATE,
) -> None:
    """
    Upload a file to the SkyLock.
    """
    privacy = Privacy.PRIVATE
    if not file_path.exists():
        typer.secho(f"File {file_path} does not exist.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not file_path.is_file():
        typer.secho(f"{file_path} is not a file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    new_file = file_operations.upload_file(file_path, destination_path, force, privacy)
    pwd()
    typer.secho(
        f"File {new_file.name} uploaded to {new_file.path} successfully",
        fg=typer.colors.GREEN,
    )
    typer.secho(
        f"Visibility: {new_file.visibility_label}",
        fg=new_file.visibility_color,
    )


@app.command()
def download(
    file_path: Annotated[Path, typer.Argument(help="The path of the file to download")],
) -> None:
    """
    Download a file from the SkyLock.
    """
    file_path = file_operations.download_file(file_path)
    pwd()
    typer.secho(
        f"File {file_path.name} downloaded successfully to {typer.style(file_path.parent, fg=typer.colors.CYAN, underline=True)}",
        fg=typer.colors.GREEN,
    )


@app.command()
def set_url(
    base_url: Annotated[
        Optional[str], typer.Argument(help="The URL of the SkyLock server")
    ] = None,
) -> None:
    """
    Set the URL of the SkyLock server.
    """
    new_context = url_manager.set_url(base_url)
    typer.secho(
        f"Base URL set to {typer.style(new_context.base_url, fg=typer.colors.CYAN, underline=True)}",
        fg=typer.colors.GREEN,
    )


@app.command()
def get_url() -> None:
    """
    Get the URL of the SkyLock server.
    """
    base_url = url_manager.get_url()
    typer.secho(
        f"SkyLock API base URL: {typer.style(base_url, fg=typer.colors.CYAN, underline=True)}",
        fg=typer.colors.GREEN,
    )


@app.command()
def share(
    resource_path: Annotated[
        str,
        typer.Argument(
            help="The path of the resource to share. If you want to share a directory, the path must end with /"
        ),
    ],
    mode: Annotated[
        Privacy,
        typer.Option(
            "--mode", help="Visibility mode: 'protected', 'public', or 'private'"
        ),
    ] = Privacy.PRIVATE,
    users: Annotated[
        Optional[str],
        typer.Option(
            "--to",
            help="Space-separated list of usernames to share with (for 'protected' mode)",
        ),
    ] = None,
) -> None:
    """
    Share a resource.
    """
    user_list = []

    if mode == Privacy.PROTECTED:
        if not users:
            typer.secho(
                "Error: Usernames are required for 'protected' mode.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        user_list = [u.strip() for u in users.split(",")]
    resource = file_operations.change_file_visibility(resource_path, mode, user_list)

    share_link = (
        dir_operations.share_directory(resource_path)
        if path_parser.is_directory(resource_path)
        else file_operations.share_file(resource_path)
    )
    typer.secho(
        f"{resource.type_label.capitalize()} {resource.path} is now {resource.visibility_label}",
        fg=resource.visibility_color,
    )
    pwd()
    typer.secho(
        f"URL to shared resource: {typer.style(share_link.url, fg=typer.colors.CYAN, underline=True)}",
        fg=typer.colors.GREEN,
    )

@app.command()
def zip(
    dir_path: Annotated[
        str,
        typer.Argument(
            help="The path of the directory to zip. Must not end with /."
        ),
    ],
) -> None:
    created_file = dir_operations.zip_directory(directory_path=dir_path)
    typer.secho(
        f"Created file: {typer.style(created_file.name, fg=created_file.color)}",
        fg=typer.colors.GREEN,
    )

if __name__ == "__main__":
    app()
