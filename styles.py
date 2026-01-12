from fasthtml.common import Style

css = Style(
    """
    /* NOTE:
       Avoid overriding UIkit's `uk-switcher` visibility rules globally.
     */

    /* Markdown styling */
    .prose h1, .prose h2, .prose h3, .prose h4 { 
        margin-top: 1em; margin-bottom: 0.5em; font-weight: 600; 
        color: hsl(var(--foreground)); 
    }
    .prose h1 { font-size: 1.5em; }
    .prose h2 { font-size: 1.25em; }
    .prose h3 { font-size: 1.1em; }
    .prose p { margin-bottom: 0.75em; line-height: 1.6; color: hsl(var(--foreground)); }
    
    .prose ul, .prose ol { margin-left: 1.5em; margin-bottom: 0.75em; padding-left: 0.5em; }
    .prose ul { list-style-type: disc; }
    
    .prose li { margin-bottom: 0.25em; line-height: 1.5; color: hsl(var(--foreground)); }
    .prose li::marker { color: hsl(var(--muted-foreground)); } 
    
    .prose code { 
        /* Use 'muted' for code background */
        background: hsl(var(--muted)); 
        color: hsl(var(--foreground));
        padding: 0.15em 0.4em; border-radius: var(--uk-global-radius-s); font-size: 0.9em; 
    }
    
    .prose pre { 
        /* Use 'card' for code blocks */
        background: hsl(var(--card)); 
        padding: 1em; border-radius: var(--uk-global-radius); overflow-x: auto; margin-bottom: 1em; 
        border: 1px solid hsl(var(--border));
    }
    .prose pre code { background: none; padding: 0; color: inherit; }
    
    .prose blockquote { 
        border-left: 3px solid hsl(var(--primary)); 
        padding-left: 1em; margin-left: 0; font-style: italic; 
        color: hsl(var(--muted-foreground));
    }
    
    .prose table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
    .prose th, .prose td { 
        border: 1px solid hsl(var(--border)); 
        padding: 0.5em; text-align: left; 
    }
    .prose strong { font-weight: 600; color: hsl(var(--foreground)); }

    /* Thinking block styling */
    .thinking-block { 
        margin-bottom: 1em; 
        border: 1px solid hsl(var(--border)); 
        border-radius: var(--uk-global-radius); 
        background: hsl(var(--muted) / 0.3); /* Opacity applied to variable */
    }
    .thinking-summary { 
        cursor: pointer; padding: 0.75em 1em; font-weight: 500; 
        color: hsl(var(--muted-foreground)); 
        user-select: none; 
    }
    .thinking-summary:hover { color: hsl(var(--foreground)); }
    
    .thinking-content { 
        padding: 0 1em 1em 1em; font-size: 0.9em; 
        color: hsl(var(--muted-foreground)); 
        border-top: 1px solid hsl(var(--border)); 
    }

    /* Skeleton loading animation */
    @keyframes skeleton-pulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 0.7; }
    }
    .skeleton-bar {
        /* Gradient using muted and accent colors */
        background: linear-gradient(90deg, hsl(var(--muted)) 0%, hsl(var(--accent)) 50%, hsl(var(--muted)) 100%);
        background-size: 200% 100%;
        animation: skeleton-pulse 1.5s ease-in-out infinite;
        border-radius: var(--uk-global-radius-s);
        height: 12px;
        margin-bottom: 8px;
    }

    /* Transcript viewer styles */
    .transcript-viewer {
        max-height: 65vh;
        overflow-y: auto;
        border-radius: var(--uk-global-radius);
        border: 1px solid hsl(var(--border));
        background: hsl(var(--background));
    }
    .transcript-header {
        position: sticky;
        top: 0;
        /* Using background with 95% opacity for blur effect */
        background: hsl(var(--background) / 0.95);
        padding: 1rem;
        border-bottom: 1px solid hsl(var(--border));
        z-index: 10;
        backdrop-filter: blur(8px);
    }
    .transcript-meta {
        display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.85rem;
        color: hsl(var(--muted-foreground));
    }
    
    .transcript-segment {
        display: grid; grid-template-columns: 80px 1fr; gap: 0.75rem;
        padding: 0.6rem 0.75rem; border-radius: var(--uk-global-radius); margin-bottom: 0.15rem;
        transition: background 0.15s ease;
        content-visibility: auto; contain-intrinsic-size: 60px;
    }
    .transcript-segment:hover {
        background: hsl(var(--muted));
    }
    
    .segment-time {
        font-family: 'JetBrains Mono', 'SF Mono', monospace;
        font-size: 0.7rem;
        color: hsl(var(--muted-foreground));
        padding-top: 0.2rem; text-align: right;
    }
    
    .segment-speaker {
        font-weight: 600; font-size: 0.8rem; letter-spacing: 0.02em;
        color: hsl(var(--foreground));
    }

    .segment-text {
        font-size: 0.875rem; line-height: 1.55;
        color: hsl(var(--foreground));
    }
    """
)
