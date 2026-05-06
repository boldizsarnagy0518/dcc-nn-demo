# Vercel Deployment Guide For The NN Mockup

This guide is for hosting the clickable NN mockup page that the QR code will open.

## What To Deploy

Deploy the **whole repository** to Vercel.

The important files for the hosted mockup are:

```text
vercel.json
nn_actionable_site/index.html
nn_actionable_site/styles.css
nn_actionable_site/app.js
nn_actionable_site/NN-logo.png
```

The Python evidence pipeline does not need to run on Vercel. Vercel is only for the static, QR-code-friendly mockup site.

## Vercel Settings

Use these settings:

```text
Framework Preset: Other
Build Command: leave empty
Output Directory: leave empty
Install Command: leave empty
Root Directory: repository root
```

The root `vercel.json` already routes `/` to:

```text
nn_actionable_site/index.html
```

It also routes:

```text
/styles.css -> nn_actionable_site/styles.css
/app.js -> nn_actionable_site/app.js
/NN-logo.png -> nn_actionable_site/NN-logo.png
```

## After Deploy

Open the Vercel URL:

```text
https://<project-name>.vercel.app/
```

Check these routes in the browser:

```text
/
/#calculators
/#pages
/#trust
/#support
/#documents
```

The QR code should point to the root Vercel URL:

```text
https://<project-name>.vercel.app/
```

## What Not To Upload Separately

Do not upload `.env`.

Do not upload generated evidence outputs unless you explicitly want them in the repository:

```text
results/controlled_ab_<timestamp>/
```

The hosted mockup does not need API keys or generated Excel results.

## Final Demo Story

Use Vercel for the user-facing mockup:

```text
Scan QR code -> open the NN-style mockup -> test calculators and rewritten product-page sections.
```

Use the controlled A/B Excel outputs separately for evidence:

```text
AB_summary.xlsx -> shows whether the actionable recommendations improved answer quality, citation readiness and next-step actionability.
```
