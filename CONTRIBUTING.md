# Contributing To API_Translate

## Getting Started
- Fork the repository and create a feature branch
- Install Python dependencies with `pip install -r requirements.txt`
- Install frontend dependencies with `cd frontend && npm install`
- Run the backend with `python main.py --reload`
- Run the frontend with `cd frontend && npm run dev`

## Development Expectations
- Keep backend modules focused and typed
- Keep React components small and reusable
- Do not expose raw provider keys in logs, APIs, or UI
- Add or update tests when behavior changes
- Update docs when routes, deployment behavior, or provider flows change

## Pull Requests
- Describe the user-facing goal clearly
- Include notes about testing performed
- Add screenshots for UI changes when relevant
- Avoid unrelated refactors in feature PRs

## Suggested Workflow
```bash
python -m pytest
cd frontend
npm run check
npm run build
```
