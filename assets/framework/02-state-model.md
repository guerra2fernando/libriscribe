# State Model

## `state.json` Fields

| Field | Type | Description |
|---|---|---|
| `bookIdeaName` | string | Original user-provided book project name |
| `sanitizedBookIdeaName` | string | Filesystem-safe slug |
| `bookIdeaMemoryFolder` | string | Path to the book-idea folder under `.spec/` |
| `currentStage` | string | Active stage ID or `"none"` after finalization |
| `completedSteps` | string[] | Ordered list of completed stage IDs |
| `incompletedStages` | string[] | Stages skipped or force-bypassed |
| `nextRecommendedStep` | string | Human-readable next action |
| `lastUpdatedBy` | string | Agent or CLI that last updated state |
| `lastUpdatedAt` | ISO8601 | Timestamp of last state write |
| `initialized` | boolean | True once init has run |
| `finalized` | boolean | True once stage 6 has been explicitly confirmed |
| `orchestrationMode` | `"parallel"` or `"sequential"` | Detected at init time |
| `chapterCount` | number | Number of chapters in the approved outline |
| `manuscriptFile` | string or null | Path to the final manuscript once assembled |

## State Categories

| Category | `currentStage` value | Description |
|---|---|---|
| Uninitialized | n/a | No `state.json` exists yet |
| Initialized | `1-book-init` | Book idea created, stage 1 active |
| In-progress | any stage ID | Work underway in current stage |
| Stage complete | same stage ID | Stage finished, awaiting user advancement |
| Finalized | `"none"` | Stage 6 explicitly confirmed by user |

## `00-current-status.md` Required Fields

- `Current book idea`
- `Current stage`
- `Completed steps`
- `Incompleted stages`
- `Next recommended step`
- `Status note`
- `Blockers / warnings`
- `Last updated by`
- `Last updated at`
