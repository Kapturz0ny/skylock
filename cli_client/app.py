import typer
from rich import print

app = typer.Typer()

@app.command()
def hello(name: str):
    print(f"Hello {name}!")

@app.command()
def goodbye(name: str):
    print(f"Goodbye {name}!")

if __name__ == "__main__":
    app()