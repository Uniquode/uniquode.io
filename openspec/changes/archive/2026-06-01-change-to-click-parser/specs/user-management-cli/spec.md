## ADDED Requirements

### Requirement: User manager Click parser
The system SHALL use Click for the `usermgr` command parser while preserving the
existing local operator command interface and management outcomes.

#### Scenario: User manager subcommands remain available
- **WHEN** an operator runs `usermgr create`, `usermgr update`, `usermgr delete`,
  `usermgr deactivate`, `usermgr list`, or `usermgr password`
- **THEN** the command accepts the same command names, positional arguments, and
  option names as before the parser migration

#### Scenario: Password source semantics remain protected
- **WHEN** an operator supplies `--password -`
- **THEN** the command reads exactly one non-empty line from non-interactive
  stdin and rejects interactive stdin or extra trailing input
- **AND** when an operator omits the password source or supplies `--password`
  without a value, the command uses a hidden confirmation prompt
- **AND** direct command-line password values other than `-` or the prompt
  sentinel are rejected

#### Scenario: User manager outputs remain compatible
- **WHEN** user-management operations succeed or fail
- **THEN** the command preserves the existing human, JSON, and CSV output
  contracts and returns the same success or failure exit status as before the
  parser migration
