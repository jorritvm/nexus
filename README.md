# Nexus
A configuration manager for python code. 

Meant to reduce the amount of developer code needed to get a flexible python application configuration up and running.

<!-- TOC -->
* [Nexus](#nexus)
  * [Features](#features)
  * [Concepts](#concepts)
    * [Configuration levels](#configuration-levels)
    * [Type safety](#type-safety)
    * [Unified configuration model](#unified-configuration-model)
  * [Author](#author)
<!-- TOC -->

## Features
- ✅ Supports command line arguments
- ✅ Supports environment variables
- ✅ Support environment variables from .env files
- ✅ Supports YAML configuration files
- ✅ Support default values in code
- ✅ Type safe configuration values
- ✅ Fail early
- ✅ Priority based merge of multiple configuration sources
- ✅ Easy to use API

## Concepts
### Configuration levels
There are 2 levels of configuration supported by this library.
- Application level configuration: Configuration that is global to the entire application. 
- Runtime level configuration: Configuration that is specific to a particular runtime/entrypoint of the application.

### Type safety
The developer defines pydantic models for the configuration structure. This ensures type safety and validation of configuration values.

### Unified configuration model
Unification happens on 2 levels:
- Application level and runtime level configuration are merged into a single configuration model. Duplicate keys are resolved by giving priority to runtime level configuration.
- Multiple sources are merged into a single unified configuration model. The sources are prioritized in the following order (highest to lowest):
  - Command line arguments
  - Environment variables
  - .env files
  - YAML configuration files
  - Default values in code

## Author
Jorrit Vander Mynsbrugge