"""CSS styles for the Contract Assistant UI."""

from __future__ import annotations


OVERVIEW_CSS = """
.landing-layout,
.workspace-layout {
    display: flex;
    flex-direction: column;
    gap: 24px;
    max-width: 1080px;
    margin: 0 auto;
}

.landing-hero {
    position: relative;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 32px;
    padding: 48px 48px 12px;
    border-radius: 28px;
    background: linear-gradient(130deg, #f4f8ff 0%, #eef3ff 40%, #fef7f2 100%);
    box-shadow: 0 30px 70px rgba(15, 23, 42, 0.12);
    overflow: hidden;
    align-items: stretch;
}

.landing-hero::after {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.18), transparent 55%),
                radial-gradient(circle at 85% 25%, rgba(59, 130, 246, 0.24), transparent 60%),
                radial-gradient(circle at 50% 85%, rgba(248, 113, 113, 0.14), transparent 55%);
    pointer-events: none;
    opacity: 0.9;
}

.landing-hero__copy,
.landing-hero__panel,
.workspace-hero__copy,
.workspace-hero__metrics {
    position: relative;
    z-index: 1;
}

.landing-hero__copy,
.workspace-hero__copy {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.landing-hero__title,
.workspace-hero__title {
    font-size: clamp(2.4rem, 3.6vw, 3.4rem);
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 16px;
}

.landing-hero__subtitle,
.workspace-hero__subtitle {
    font-size: 1.08rem;
    color: #1e293b;
    margin: 0 0 28px;
    line-height: 1.6;
}

.landing-hero__highlights,
.workspace-hero__highlights {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    gap: 22px;
}

.landing-hero__highlights li,
.workspace-hero__highlights li {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    font-size: 0.98rem;
    color: #1e293b;
    line-height: 1.65;
}

.landing-hero__highlights li strong,
.workspace-hero__highlights li strong {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.01em;
}

.landing-hero__highlights li::before,
.workspace-hero__highlights li::before {
    content: "●";
    color: #4f46e5;
    font-size: 0.9rem;
    line-height: 1.6;
    flex-shrink: 0;
    margin-top: 0.35rem;
}

.landing-hero__panel {
    display: grid;
    gap: 16px;
    grid-auto-rows: auto;
    align-content: start;
}

.landing-hero__panel-card {
    background: rgba(255, 255, 255, 0.88);
    border-radius: 20px;
    padding: 24px;
    border: 1px solid rgba(148, 163, 184, 0.24);
    box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
    backdrop-filter: blur(6px);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.landing-hero__panel-card h4 {
    margin: 0 0 8px;
    font-size: 1rem;
    color: #1e293b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.landing-hero__panel-card strong {
    display: block;
    font-size: 1.75rem;
    color: #111827;
    margin-bottom: 6px;
}

.landing-hero__panel-card p {
    margin: 0;
    font-size: 0.95rem;
    color: #4b5563;
}

.landing-section,
.workspace-section {
    display: grid;
    gap: 24px;
    background: #ffffff;
    border-radius: 24px;
    padding: 32px;
    border: 1px solid rgba(148, 163, 184, 0.22);
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

.landing-section__header h2,
.workspace-section__header h2 {
    margin: 0 0 12px;
    font-size: 1.6rem;
    color: #0f172a;
}

.landing-section__header p,
.workspace-section__header p {
    margin: 0;
    font-size: 1rem;
    color: #475569;
}

.landing-value-grid {
    display: grid;
    gap: 24px;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.landing-value-card {
    background: linear-gradient(165deg, #ffffff 0%, #f8fbff 100%);
    border-radius: 20px;
    padding: 28px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.landing-value-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 26px 44px rgba(15, 23, 42, 0.12);
}

.landing-value-card h3 {
    margin: 0 0 12px;
    font-size: 1.2rem;
    color: #1e293b;
}

.landing-value-card p {
    margin: 0 0 16px;
    font-size: 0.98rem;
    color: #4b5563;
    line-height: 1.6;
}

.landing-value-card ul {
    margin: 0;
    padding-left: 20px;
    color: #475569;
    display: grid;
    gap: 8px;
    font-size: 0.95rem;
}

.landing-process {
    background: linear-gradient(140deg, #0f172a 0%, #1e293b 60%, #1e3a8a 100%);
    color: #e2e8f0;
}

.landing-process__header h2 {
    margin: 0 0 10px;
    font-size: 1.6rem;
    color: #f8fafc;
}

.landing-process__header p {
    margin: 0;
    font-size: 1rem;
    color: rgba(226, 232, 240, 0.8);
}

.landing-process__timeline {
    counter-reset: steps;
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 18px;
}

.landing-process__timeline li {
    position: relative;
    padding-left: 78px;
    min-height: 64px;
}

.landing-process__timeline li::before {
    counter-increment: steps;
    content: counter(steps);
    position: absolute;
    top: 2px;
    left: 0;
    width: 52px;
    height: 52px;
    border-radius: 18px;
    background: rgba(59, 130, 246, 0.25);
    color: #e0f2fe;
    font-weight: 700;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(59, 130, 246, 0.45);
    box-shadow: inset 0 0 0 2px rgba(14, 116, 144, 0.3);
}

.landing-process__timeline strong {
    display: block;
    font-size: 1.05rem;
    margin-bottom: 6px;
    color: #f8fafc;
}

.landing-process__timeline span {
    display: block;
    font-size: 0.95rem;
    color: rgba(226, 232, 240, 0.8);
    line-height: 1.6;
}

.landing-behind {
    display: grid;
    gap: 18px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.landing-behind__card {
    background: linear-gradient(165deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 18px;
    padding: 24px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
}

.landing-behind__card h4 {
    margin: 0 0 10px;
    font-size: 1.08rem;
    color: #0f172a;
}

.landing-behind__card p {
    margin: 0;
    font-size: 0.95rem;
    color: #475569;
    line-height: 1.55;
}

.workspace-hero {
    position: relative;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 28px;
    padding: 36px;
    border-radius: 26px;
    background: linear-gradient(130deg, #eef2ff 0%, #f8fafc 55%, #fef3f2 100%);
    box-shadow: 0 24px 56px rgba(15, 23, 42, 0.1);
    overflow: hidden;
    align-items: start;
}

.workspace-hero--draft {
    background: linear-gradient(130deg, #e0f2fe 0%, #f5faff 55%, #fef3f2 100%);
}

.workspace-hero--assistant {
    background: linear-gradient(130deg, #ede9fe 0%, #f5f3ff 55%, #ecfeff 100%);
}

.workspace-hero--dashboard {
    background: linear-gradient(130deg, #e0f2fe 0%, #f0fdf4 55%, #fff7ed 100%);
}

.workspace-hero__metrics {
    display: grid;
    gap: 16px;
}

.metrics-tiles {
    display: grid;
    gap: 18px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.metrics-tile {
    background: linear-gradient(165deg, #ffffff 0%, #f8fafc 100%);
    border-radius: 18px;
    padding: 20px 22px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.metrics-tile h3 {
    margin: 0;
    font-size: 1rem;
    color: #1e293b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.metrics-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #0f172a;
}

.metrics-note {
    font-size: 0.9rem;
    color: #475569;
}

.workspace-section ul {
    margin: 0 0 14px 1.4rem;
    padding-left: 0.2rem;
}

.workspace-section ul li {
    line-height: 1.6;
}

.workspace-table table {
    table-layout: fixed;
}

.workspace-table table td,
.workspace-table table th {
    white-space: normal !important;
    word-wrap: break-word;
}

.workspace-form__row {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.workspace-form__actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.workspace-back {
    width: fit-content;
    margin-top: 8px;
}

@media (max-width: 960px) {
    .landing-hero,
    .workspace-hero {
        padding: 36px;
    }
}

@media (max-width: 720px) {
    .landing-hero,
    .workspace-hero {
        padding: 28px;
    }

    .landing-hero__title,
    .workspace-hero__title {
        font-size: 2.3rem;
    }

    .landing-section,
    .workspace-section {
        padding: 26px;
    }
}
"""
