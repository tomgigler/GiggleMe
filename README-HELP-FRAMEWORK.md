# GiggleMe help-page framework

Built against repository state:

`72b0488128b038f4b896aaeb1f98fc3b4ea45ec8`

## What this bundle adds

- `web/help/index.html`
- `web/help/styles.css`

The help page is intentionally self-contained and does not modify the existing PHP web interface.
After extracting this bundle into the GiggleMe repository root, the page should be available at `/help/` when `web/` is the site's document root.

## Framework decisions

- Organize help around user goals/features rather than reproducing the source-code command tree.
- Keep a compact slash-command reference at the bottom.
- Give each feature a stable anchor for direct links.
- Reserve clear video positions so tutorial videos can be added without redesigning the page.
- Give the two Discord-review evidence workflows permanent anchors:
  - `/help/#auto-replies`
  - `/help/#role-expansion`
- Keep Auto Replies in the regular user help because configuration is now slash-command based.
- Keep Legacy / Raw+ as an advanced migration workflow rather than presenting it as the primary interface.

## Video placeholders

The current placeholders are ordinary HTML and CSS. When videos are ready, each placeholder can be replaced with an `<iframe>` or `<video>` element while keeping the surrounding guide card and anchor unchanged.
