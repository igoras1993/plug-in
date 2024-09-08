# Plug In

`plug-in` is a library that allows You to manage dependencies across  Your project
code. Usage of `plug-in` in Your apps will result in easy-to-maintain project
structure. It guides You throughout development process by bringing the
[plugin architecture]() into Your application. `plug-in` implements this architecture
for You, with explicit requirements on Your project structure.

## Project status

I am actively developing this project right now. I've implemented the basic
functionalities and still working on API. Right now, project is
in **alpha phase**.


## Project goals

- Supply SDK for inversion of control
- Familiar for python developers
- Fully typed
- Mix best things from IoC and python code style
- Async support
- Small codebase

## Contributing

### How to start

...

### Commits
All commits should be structured according to [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/).

For answer "Which one commit type should I use?", please refer to below table.

#### Commit types

| Commit Type | Title                    | Description                                                                                                 |
|:-----------:|--------------------------|-------------------------------------------------------------------------------------------------------------|
|   `feat`    | Features                 | A new feature                                                                                               |
|    `fix`    | Bug Fixes                | A bug Fix                                                                                                   |
|   `docs`    | Documentation            | Documentation only changes                                                                                  |
|   `style`   | Styles                   | Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)      |
| `refactor`  | Code Refactoring         | A code change that neither fixes a bug nor adds a feature                                                   |
|   `perf`    | Performance Improvements | A code change that improves performance                                                                     |
|   `test`    | Tests                    | Adding missing tests or correcting existing tests                                                           |
|   `build`   | Builds                   | Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)         |
|    `ci`     | Continuous Integrations  | Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs) |
|   `chore`   | Chores                   | Other changes that don't modify src or test files                                                           |
|  `revert`   | Reverts                  | Reverts a previous commit                                                                                   |

Source: https://github.com/pvdlg/conventional-changelog-metahub/blob/master/README.md#commit-types
