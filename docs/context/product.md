# Product context

Agentic Starter provides engineering invariants, navigation integration and safe installation/update tooling. Upstream skills own development workflows. Local Markdown tracking keeps work independent of the Git hosting provider.

## Language

**Maintainer checkout**:
The starter's own source repository, where the starter's implementation is developed and released.
_Avoid_: starter repo, source checkout

**Consumer project**:
Any project with the starter installed, whether it arrived by generation or adoption.
_Avoid_: generated application, adopted project, existing project (as distinct kinds)

**Installation route**:
How a consumer project obtained the starter: generation for a new project, adoption for an existing one.

**Installation role**:
The recorded standing of an installation: maintainer checkout or consumer project.

**Managed implementation**:
Starter-owned files in a consumer project that the starter replaces on update and the project does not edit.
_Avoid_: installed tooling, engineering files

**Project configuration**:
Starter settings owned by the project, which the starter validates and migrates but does not overwrite.
_Avoid_: engineering config

**Navigation**:
Optional derived knowledge of code structure, supplied by a navigation provider (Graft) or absent (`none`), in which case agents search and read source directly.
_Avoid_: indexing, graph (as the feature name)

**Optional capability**:
A feature a project enables deliberately, whose dependencies and gate obligations exist only while it is enabled.

**Capability content**:
Managed content an optional capability's dependency installs together while the capability is enabled and an update removes after it is disabled, such as Graft's launcher, skill, package pins and agent-policy navigation section. Project data it produced, such as the Graft index, is not capability content.

**Maintainer source**:
Content in the maintainer checkout that becomes managed implementation or proves it: templates, managed implementation, maintainer tests and evals.
