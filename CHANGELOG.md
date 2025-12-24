# Changelog

## [0.4.0] 
### Added
- Traceability of configuration values via the new `_CONFIG_EXTENDED` variable, which records the value and its source for each config field.
- Support for loading configuration from JSON files, with nested structures serialized as JSON strings for compatibility with Pydantic models.

### Changed
- Refactored file loading logic to use dedicated loader functions for YAML, JSON, and ENV files.

---

## [0.3.0]
### Added
- Expose the entire public API of the `config` module at the package level, so you can use `import nexus as nx` and call `nx.setup()`, `nx.CONFIG`, etc., directly.
- Added a stable proxy object for `CONFIG` to ensure `from nexus.config import CONFIG` always points to the latest configuration instance, even after updates.

### Changed
- Updated README with new usage patterns, a minimal example and clear explanation of the proxy and package-level API.

### Fixed
- Type coercion for environment variables and .env file values now uses Pydantic parsing to ensure correct types (e.g., int fields remain int).

---


## [0.2.0]
### Added
- Added support for merging app and runtime config models, with runtime config taking precedence for overlapping keys.
- Improved CLI argument help formatting (shows `VALUE` as placeholder).
- Added support for .env files, YAML files, environment variables, and CLI arguments, with clear priority order.


### Changed
- Refactored API to allow both all-in-one `setup()` and stepwise `setup_*` methods.

---

## [0.1.0]
First version, supports basic configuration loading from YAML files.
