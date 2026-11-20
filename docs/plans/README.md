# Plans

Each file is the implementation plan for one issue, written by `/daedalus:plan`; the pre-edit hook opens code edits once it is committed on the issue branch.

| Folder | Artifact | Accepted by |
|---|---|---|
| `docs/intents/` | `<issue>_<slug>.md`: the problem and the outcome a Feature needs | the operator's approval in the conversation, recorded by its commit on the issue branch |
| `docs/specs/` | `<issue>_<slug>.md`: requirements and design for a Feature | the operator's approval in the conversation, recorded by its commit on the issue branch |
| `docs/plans/` | `<issue>_<slug>.md`: the implementation plan, with its architect review | the operator's approval in the conversation, recorded by its commit on the issue branch; merged with the change |
| `docs/decisions/` | `NNNN_<slug>.md`: one architecture decision | the operator, with the spec or plan it is committed with; immutable once on the default branch except for supersession |

`python -m daedalus check-docs` validates every artifact here; the daedalus hooks validate each one as it is edited.
