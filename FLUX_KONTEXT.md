### Base model IDs
* `black-forest-labs/flux-kontext-pro`
* `black-forest-labs/flux-kontext-max`

### Generic parameters
```json
{
  "prompt": "string",          // required
  "image": "URL | base64",
  "model_version": "flux-kontext-pro|max",
  "strength": 0.6,              // 0–1 edit strength
  "seed": null                  // optional for determinism
}
```

### Prompt templates per category

| Category | Template                                                    |
| -------- | ----------------------------------------------------------- |
| Style    | `{{style}} painting, keep composition`                      |
| Object   | `Replace {{object}} with {{new}} while preserving lighting` |
| Text     | `"replace '{{old}}' with '{{new}}'"`                        |
| BG Swap  | `Change background to {{bg}}, keep subject position`        |
| Face     | `Add {{effect}} to the face, preserve identity`             |
``` 