# GitHub Pages Deployment

This Excel Office Add-in frontend deploys its static frontend build from `frontend/dist` through GitHub Actions Pages deployment.

## URLs

- Root URL: `https://qurbaneliii.github.io/excel-plugin/`
- Taskpane URL: `https://qurbaneliii.github.io/excel-plugin/taskpane.html`

## Notes

- `index.html` exists only to prevent a GitHub Pages root `404` and redirect users to `taskpane.html`.
- `taskpane.html` remains the real Excel task pane entrypoint.
- The GitHub Pages workflow builds the frontend from `frontend/` and uploads `frontend/dist`.
- The Pages build uses a GitHub Pages base path of `/excel-plugin/` so built asset URLs resolve correctly under the repository subpath.
