from fasthtml.common import Style

css = Style(
    """
    /* NOTE:
       Avoid overriding UIkit's `uk-switcher` visibility rules globally.
       The right panel uses `uk-tab` + `uk-switcher`, and forcing `display:flex`
       on `.uk-switcher` or its inactive children will show *both* tabs at once.
     */
    /* Markdown styling */
    .prose h1, .prose h2, .prose h3, .prose h4 { margin-top: 1em; margin-bottom: 0.5em; font-weight: 600; }
    .prose h1 { font-size: 1.5em; }
    .prose h2 { font-size: 1.25em; }
    .prose h3 { font-size: 1.1em; }
    .prose p { margin-bottom: 0.75em; line-height: 1.6; }
    .prose ul, .prose ol { margin-left: 1.5em; margin-bottom: 0.75em; padding-left: 0.5em; }
    .prose ul { list-style-type: disc; }
    .prose ul ul { list-style-type: circle; }
    .prose ul ul ul { list-style-type: square; }
    .prose ol { list-style-type: decimal; }
    .prose ol ol { list-style-type: lower-alpha; }
    .prose ol ol ol { list-style-type: lower-roman; }
    .prose li { margin-bottom: 0.25em; line-height: 1.5; }
    .prose li::marker { color: rgba(255,255,255,0.7); }
    .prose code { background: rgba(0,0,0,0.2); padding: 0.15em 0.4em; border-radius: 4px; font-size: 0.9em; }
    .prose pre { background: rgba(0,0,0,0.3); padding: 1em; border-radius: 6px; overflow-x: auto; margin-bottom: 1em; }
    .prose pre code { background: none; padding: 0; }
    .prose blockquote { border-left: 3px solid rgba(255,255,255,0.3); padding-left: 1em; margin-left: 0; font-style: italic; }
    .prose table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
    .prose th, .prose td { border: 1px solid rgba(255,255,255,0.2); padding: 0.5em; text-align: left; }
    .prose strong { font-weight: 600; }
    /* Thinking block styling */
    .thinking-block { margin-bottom: 1em; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; background: rgba(0,0,0,0.15); }
    .thinking-summary { cursor: pointer; padding: 0.75em 1em; font-weight: 500; color: rgba(255,255,255,0.7); user-select: none; }
    .thinking-summary:hover { color: rgba(255,255,255,0.9); }
    .thinking-content { padding: 0 1em 1em 1em; font-size: 0.9em; color: rgba(255,255,255,0.65); border-top: 1px solid rgba(255,255,255,0.1); }
    details[open] .thinking-summary { border-bottom: none; }
    /* Skeleton loading animation */
    @keyframes skeleton-pulse {
        0%, 100% { opacity: 0.4; }
        50% { opacity: 0.7; }
    }
    .skeleton-bar {
        background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 100%);
        background-size: 200% 100%;
        animation: skeleton-pulse 1.5s ease-in-out infinite;
        border-radius: 4px;
        height: 12px;
        margin-bottom: 8px;
    }
    /* Clean transcript row styling - no borders */
    .transcript-checkbox-wrapper {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
    }
    .transcript-checkbox-wrapper label {
        border: none !important;
        background: transparent !important;
    }
    /* Transcript viewer styles */
    .transcript-viewer {
        max-height: 65vh;
        overflow-y: auto;
        border-radius: 8px;
    }
    .transcript-header {
        position: sticky;
        top: 0;
        background: rgba(30, 30, 35, 0.98);
        padding: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        z-index: 10;
        backdrop-filter: blur(8px);
    }
    .transcript-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
    }
    .transcript-meta-item {
        display: flex;
        gap: 0.5rem;
    }
    .transcript-meta-label {
        color: rgba(255,255,255,0.4);
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.05em;
    }
    .transcript-content {
        padding: 0.5rem;
    }
    .transcript-segment {
        display: grid;
        grid-template-columns: 80px 1fr;
        gap: 0.75rem;
        padding: 0.6rem 0.75rem;
        border-radius: 6px;
        margin-bottom: 0.15rem;
        transition: background 0.15s ease;
        /*
          Performance: transcripts can be very long, and each segment is multiple DOM nodes.
          `content-visibility: auto` lets the browser skip rendering off-screen segments,
          which significantly reduces tab-switch jank and improves scroll performance.
        */
        content-visibility: auto;
        contain-intrinsic-size: 60px;
    }
    .transcript-segment:hover {
        background: rgba(255,255,255,0.03);
    }
    .segment-time {
        font-family: 'JetBrains Mono', 'SF Mono', monospace;
        font-size: 0.7rem;
        color: rgba(255,255,255,0.35);
        padding-top: 0.2rem;
        text-align: right;
    }
    .segment-body {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }
    .segment-speaker {
        font-weight: 600;
        font-size: 0.8rem;
        letter-spacing: 0.02em;
    }
    .segment-text {
        font-size: 0.875rem;
        line-height: 1.55;
        color: rgba(255,255,255,0.85);
    }
    /* Speaker colors */
    .speaker-0 { color: #f59e0b; }
    .speaker-1 { color: #10b981; }
    .speaker-2 { color: #6366f1; }
    .speaker-3 { color: #ec4899; }
    .speaker-4 { color: #14b8a6; }
    .speaker-5 { color: #f97316; }
    .speaker-6 { color: #8b5cf6; }
    .speaker-7 { color: #06b6d4; }
    .transcript-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 0.6rem;
        padding-top: 0.6rem;
        border-top: 1px solid rgba(255,255,255,0.08);
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.75rem;
    }
    .legend-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
    }
    .view-btn {
        cursor: pointer;
        opacity: 0.4;
        transition: opacity 0.15s ease;
        font-size: 0.9rem;
        padding: 0.2rem 0.4rem;
    }
    .view-btn:hover {
        opacity: 1;
    }
    .transcript-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
    }
"""
)
