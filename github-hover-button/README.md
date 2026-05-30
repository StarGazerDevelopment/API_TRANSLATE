# GitHub Hover Button

Reusable hover-expanding GitHub button for any web project.

## Files
- `styles.css`: Button styles
- `github.svg`: Icon
- `index.html`: Demo page

## Usage (HTML)
1. Copy `styles.css` and `github.svg` into your project
2. Add the anchor:
```
<link rel="stylesheet" href="styles.css">
<a class="github-btn" href="https://github.com/StarGazerDevelopment" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
  <img src="github.svg" alt="" width="20" height="20">
  <span>GitHub</span>
</a>
```

## Usage (React/Next)
```
import './styles.css'

export function GitHubButton() {
  return (
    <a className="github-btn" href="https://github.com/StarGazerDevelopment" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
      <img src="/github.svg" alt="" width={20} height={20} />
      <span>GitHub</span>
    </a>
  )
}
```
