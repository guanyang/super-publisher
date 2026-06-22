---
name: excalidraw-visual-designer
description: Create and revise editable visual drawings directly in the Excalidraw website through the in-app browser. Use when the user asks Codex to draw in Excalidraw or update an Excalidraw canvas, including diagrams, flowcharts, architecture sketches, process maps, infographics, teaching visuals, product explanation graphics, whiteboard layouts, promotional materials, posters, flyers, menu boards, and social media graphics, especially when the output should remain editable as Excalidraw elements or imported clipboard JSON.
---

# Excalidraw Visual Designer

## Core Workflow

Use the in-app browser and the existing Excalidraw tab when present.

1. Read and follow the `browser:control-in-app-browser` skill before controlling the browser.
2. Claim the existing `https://excalidraw.com/` tab instead of opening a duplicate.
3. Keep the browser visible when the user is reviewing the drawing.
4. Prefer Excalidraw clipboard JSON import over manual dragging for complex layouts.
5. After each substantial visual change, take a screenshot and inspect it for legibility, overlap, and visual quality.
6. Finalize with the Excalidraw tab kept as `deliverable`.

## Output Types

Choose the structure by intent:

- Diagrams and flowcharts: use editable Excalidraw rectangles, diamonds, arrows, swimlanes, labels, and grouping.
- Architecture or system maps: use consistent containers, call paths, data stores, boundaries, and directional arrows.
- Infographics and teaching visuals: combine editable text/cards with simple charts, numbered sections, icons, and callouts.
- Product or object explanation graphics: use clean SVG image elements for polished product/object illustrations, then layer editable labels and arrows.
- Whiteboard sketches: keep a looser Excalidraw style, but still preserve alignment, spacing, and clear reading order.
- Promotional materials and posters: use structured panels, headline, offer, main visual, information blocks, and CTA.

Use editable Excalidraw text and shape elements for copy, labels, arrows, process structure, prices, CTA, and layout blocks. Use embedded SVG image elements only when a detailed illustration would look crude if built from primitive Excalidraw shapes.

## Visual Construction Rules

- Use a constrained canvas area or frame-like boundary for presentation graphics.
- Establish a clear reading path before placing decorative details.
- Keep text editable wherever future changes are likely.
- Prefer simple, recognizable symbols over overdrawn illustration.
- Use polished SVG image elements for food, people, products, devices, and other high-detail visuals.
- Keep stroke weights consistent within each visual region.
- Avoid floating labels; connect labels to targets with lines or place them in contained cards.
- Preserve existing user-approved areas when revising one problematic region.

## Connector Routing Rules

For any Excalidraw output that uses connectors, arrows, leader lines, callouts, or directional lines, route those lines before finalizing layout. This applies across all output types, including diagrams, architecture maps, process maps, infographics, product explanations, whiteboard sketches, posters, flyers, menu boards, and social graphics.

- Do not draw connectors through modules, containers, cards, text blocks, badges, product/object illustrations, photos, icons, faces, prices, CTAs, or other primary shapes.
- Use orthogonal polyline arrows with explicit intermediate points instead of diagonal shortcuts when a line would cross another meaningful visual element.
- Reserve gutters around grouped content: top/bottom lanes for cross-section calls, left/right lanes for external actors, annotations, legends, and infrastructure.
- Route many-to-many infrastructure dependencies through a bus line outside the module boundary, then branch from the bus to each external dependency.
- Prefer entering a target box from the nearest clear side. If the direct side is blocked, route around the group boundary and enter from top, bottom, or an outer side.
- Keep same-category arrows parallel where possible, with at least 20 px visual separation from module borders and labels.
- Avoid arrows that overlap text. If an arrow label is needed, put it in a small contained label near the line, not on top of another visual element.
- When a connector would cross a primary shape, first try one of these fixes: move the target, add a side bus, route around the group, split the connector into an outer lane, or reorder layers.
- If a crossing is unavoidable, make it an intentional bridge: use a lighter stroke for the background line and keep the crossing away from text.

Before importing any line-based scene, inspect the scene spec or screenshot for these common failures:

- actor/source arrows crossing target boxes;
- dependency or callout arrows crossing unrelated modules, cards, or illustrations;
- diagonal arrows cutting through large containers;
- connector endpoints landing in the middle of text;
- multiple arrows sharing the same exact segment without a bus.

## Clipboard Import

Excalidraw accepts clipboard JSON with:

```json
{
  "type": "excalidraw/clipboard",
  "elements": [],
  "files": {}
}
```

Import flow:

1. Generate or construct the clipboard JSON.
2. Write it to the browser clipboard with `tab.clipboard.writeText(...)`.
3. Click the Excalidraw canvas.
4. Press paste with the platform shortcut.
5. Press Escape after paste so the final view is not obscured by selection boxes.

## Clipboard Generator Script

This skill includes a general clipboard JSON generator. It has no business-domain defaults. Create a task-specific scene spec during the current task, then convert that spec into Excalidraw clipboard JSON.

Use the active Python interpreter for the current environment. In an activated virtual environment this is usually `python`; in other environments it may be another command. Do not hard-code a machine-specific interpreter path in the skill.

```bash
<python> scripts/make_excalidraw_clipboard.py --spec scene-spec.json --output scene.excalidraw-clipboard.json
```

If no `--spec` is provided, the script emits an empty valid clipboard payload. A minimal generic spec looks like:

```json
{
  "elements": [
    {"type": "rectangle", "x": 80, "y": 80, "width": 360, "height": 180, "backgroundColor": "#ffffff"},
    {"type": "text", "x": 110, "y": 120, "text": "Editable title", "fontSize": 32},
    {"type": "arrow", "x": 120, "y": 220, "points": [[0, 0], [180, 0]]}
  ]
}
```

## Quality Rules

Check these before finishing:

- Food, product, or object illustrations must be immediately recognizable. If a user says an illustration looks odd, replace the asset instead of defending it.
- Avoid facial-looking marks on food unless explicitly requested.
- Text must not overlap buttons, badges, drawings, arrows, or borders.
- Keep key labels readable at the current zoom.
- Use consistent stroke weights inside the same visual region.
- If a decorative detail looks crude, simplify it or replace it with a cleaner SVG image.
- For any scene with arrows or connector lines, direction and grouping must be unambiguous, and lines should avoid crossing primary visual elements.
- For posters and infographics, hierarchy must be obvious at a glance.

## Common Revision Pattern

When the user critiques one area:

1. Name the issue plainly.
2. Scope the change to that area unless the surrounding layout causes the problem.
3. Re-import a revised scene or replace the relevant element.
4. Screenshot-check the revised area and adjacent text.
5. Keep the Excalidraw tab open for further editing.
