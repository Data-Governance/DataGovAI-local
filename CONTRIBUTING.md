# Contributing to Generic AI Agent

First off, thank you for considering contributing to Generic AI Agent! It's people like you that make Generic AI Agent such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include any error messages or stack traces

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Process

1. Set up your development environment:
```bash
git clone https://github.com/yourusername/generic-ai-agent.git
cd generic-ai-agent
pip install -e ".[dev]"
```

2. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes and ensure they follow our coding standards:
```bash
# Format code
black src/ tests/
isort src/ tests/

# Run linters
flake8 src/ tests/
mypy src/

# Run tests
pytest tests/
```

4. Write or update tests as needed

5. Update documentation if necessary

6. Commit your changes:
```bash
git add .
git commit -m "feat: add your feature description"
```

7. Push to your fork and submit a pull request

## Coding Standards

* Use [Black](https://github.com/psf/black) for code formatting
* Use [isort](https://pycqa.github.io/isort/) for import sorting
* Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
* Write docstrings following [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
* Add type hints to function definitions
* Write meaningful commit messages following [Conventional Commits](https://www.conventionalcommits.org/)

## Testing

* Write unit tests for new code
* Ensure all tests pass before submitting a pull request
* Aim for high test coverage
* Use pytest fixtures and parametrize when appropriate
* Mock external dependencies

## Documentation

* Update documentation for any new features or changes
* Include docstrings for all public modules, functions, classes, and methods
* Add examples for new features
* Keep the README.md up to date

## Git Commit Messages

* Use the present tense ("add feature" not "added feature")
* Use the imperative mood ("move cursor to..." not "moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable emoji:
    * 🎨 `:art:` when improving the format/structure of the code
    * 🐎 `:racehorse:` when improving performance
    * 🚱 `:non-potable_water:` when plugging memory leaks
    * 📝 `:memo:` when writing docs
    * 🐛 `:bug:` when fixing a bug
    * 🔥 `:fire:` when removing code or files
    * 💚 `:green_heart:` when fixing the CI build
    * ✅ `:white_check_mark:` when adding tests
    * 🔒 `:lock:` when dealing with security
    * ⬆️ `:arrow_up:` when upgrading dependencies
    * ⬇️ `:arrow_down:` when downgrading dependencies

## Additional Notes

### Issue and Pull Request Labels

* `bug` - Something isn't working
* `enhancement` - New feature or request
* `documentation` - Improvements or additions to documentation
* `good first issue` - Good for newcomers
* `help wanted` - Extra attention is needed
* `question` - Further information is requested
* `wontfix` - This will not be worked on

## Recognition

Contributors will be recognized in our [CONTRIBUTORS.md](CONTRIBUTORS.md) file. Thank you for your contributions! 