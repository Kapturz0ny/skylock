# SkyLock - CLI

We created a file hosting solution that allows users to store, manage, and share their files and folders securely. This directory contains the CLI that communicates with the file hosting API to perform all operations.

## Features

This user command line interface enables to:

- **User Authentication**: Create an account (with 2FA email authentication), log in, and access your root folder containing all your files and folders.
- **Add Files and Folders**: Upload files or create folders.
- **Delete Files and Folders**: Remove any of your own files or folders.
- **Overwrite Files**: Replace your existing files with new versions.
- **Manage Folders**: Nest folders within each other and organize your files.
- **Change Visibility**: Set files to public, protected or private. Protected meaning that the file is visible only to those you pick.
- **Generate urls**: Generate urls to share private contents with your friends.
- **View Contents**: Display the contents of any folder.
- **Download Files**: Fetch your own files or publicly accessible files.
- **Create ZIP files**: Pack folders into ZIP files.
- **Download Folders**: Download entire folders as created previously ZIP files.
- **Unix-Style Navigation**: Move through your file tree using familiar Unix-style commands.

## Example usage

### Register a new user
```sh
slock register <username>
```

### Login
```sh
slock login <username>
```

This is what should appear after you login succesfully
```sh
User logged in successfully
Hello, username
Welcome to our file hosting service
 ____   _            _                   _    
/ ___| | | __ _   _ | |      ___    ___ | | __
\___ \ | |/ /| | | || |     / _ \  / __|| |/ /
 ___) ||   < | |_| || |___ | (_) || (__ |   < 
|____/ |_|\_\ \__, ||_____| \___/  \___||_|\_\
              |___/                           

Your current working directory is: /
```

### List the contents of a directory
```sh
slock ls [directory_path]
```

### Change the current working directory
```sh
slock cd [directory_path]
```

### You can run this command to get information about the usage of all commands
```sh
slock --help
```

## Configuration

The CLI automatically stores the user session and current directory context for your convenience.

## Development

To contribute or modify the CLI client, clone this repository and install the required dependencies:

```bash
git clone https://gitlab-stud.elka.pw.edu.pl/oszypczy/zprp-cli-client.git
cd zprp-cli/cli
make install
```

## Tests:

```bash
make test
```

You can test the code using mutiple Python versions using the tox tool:

```bash
tox
```

## Documentation:

```bash
make mkdocs
```

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for more details.
