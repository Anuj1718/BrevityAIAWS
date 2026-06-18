import React, { Suspense, lazy } from 'react';
import { Link } from 'react-router-dom';
import './Home.css';
import FAQ from './FAQ.jsx';

// Lazy-load the heavy Spline 3D component (~3.2 MB)
const Spline = lazy(() => import('@splinetool/react-spline'));

// ShaderGradient background for the “showcase” panel
const SHADER_URL =
  'https://www.shadergradient.co/customize?animate=on&axesHelper=off&bgColor1=%23000000&bgColor2=%23000000&brightness=0.8&cAzimuthAngle=270&cDistance=0.5&cPolarAngle=180&cameraZoom=15.1&color1=%23c46cab&color2=%23ff810a&color3=%238da0ce&destination=onCanvas&embedMode=on&envPreset=city&format=gif&fov=45&frameRate=10&gizmoHelper=hide&grain=on&lightType=env&pixelDensity=1&positionX=-0.1&positionY=0&positionZ=0&range=enabled&rangeEnd=40&rangeStart=0&reflection=0.4&rotationX=0&rotationY=130&rotationZ=70&shader=defaults&type=sphere&uAmplitude=3.2&uDensity=0.8&uFrequency=5.5&uSpeed=0.3&uStrength=0.3&uTime=0&wireframe=false';

export default function Home() {
  return (
    <div className="home">
      {/* HERO (full-bleed with scrollable Spline background) */}
      <main className="hero">
        <div className="hero-bg" aria-hidden="true">
          {/* <Spline scene="https://prod.spline.design/9VtlTTrUq9NRjQsM/scene.splinecode" />  */}
          <Suspense fallback={<div className="hero-bg-placeholder" />}>
            <Spline scene="https://prod.spline.design/9bhPBNgr9ongm3Jr/scene.splinecode"/>
          </Suspense>
        </div>
        <div className="hero-scrim" aria-hidden="true" />

        <div className="container hero-inner">
          <section className="left">
            <h1>Transform PDFs into concise summaries</h1>
            <p>
              Harness the power of AI to instantly convert lengthy documents into clear,
              actionable insights. Save time and boost productivity with context-aware
              summarization.
            </p>
            <div className="cta">
              <Link className="btn primary" to="/upload">Get started free</Link>
              {/* <Link className="btn outline" to="/login">Log in</Link> */}
            </div>
          </section>

          <section className="right-spacer" />
        </div>
      </main>

      {/* SHOWCASE PANEL (curved, with ShaderGradient background) */}
      <section className="showcase">
        <div className="showcase-bg" aria-hidden="true">
          <iframe
            className="shader-iframe"
            src={SHADER_URL}
            title="Showcase background"
            loading="lazy"
          />
          <div className="showcase-overlay" />
        </div>
        <div className="showcase-border" aria-hidden="true" />

        <div className="container showcase-inner">
          {/* How it works */}
          <h2 className="how-title">How It Works</h2>
          <p className="how-subtitle">Three simple steps to get your AI-powered summaries</p>

          <div className="cards">
            <div className="card">
              <div className="card-glow" aria-hidden="true" />
              <div className="icon-badge accent-violet"><UploadIcon /></div>
              <h3 className="card-title">Upload PDF</h3>
              <p className="card-text">
                Drag and drop your PDF or pick it from your device. We handle big files with fast, reliable uploads.
              </p>
            </div>

            <div className="card">
              <div className="card-glow" aria-hidden="true" />
              <div className="icon-badge accent-orange"><BrainIcon /></div>
              <h3 className="card-title">AI Analysis</h3>
              <p className="card-text">
                Our NLP models understand context, structure, and key points to extract what matters most.
              </p>
            </div>

            <div className="card">
              <div className="card-glow" aria-hidden="true" />
              <div className="icon-badge accent-green"><DocIcon /></div>
              <h3 className="card-title">Get Summary</h3>
              <p className="card-text">
                Instantly get a clear, concise summary with citations—ready to copy, download, or share.
              </p>
            </div>
          </div>

          {/* Features + FAQ + (optional) Home pricing */}
          <Features />
          <FAQ defaultOpen={0} />
          <HomePricing />
        </div>
      </section>
    </div>
  );
}

/* ---------- Inline icons ---------- */
function UploadIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <path d="M7 17a5 5 0 0 1 1.1-9.9A6 6 0 0 1 21 12a4 4 0 0 1-1 7.9H7.5"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 14V7m0 0l-3 3m3-3l3 3"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function BrainIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <path d="M8.5 4A3.5 3.5 0 0 0 5 7.5V16a4 4 0 0 0 4 4h1v-8H8.5A2.5 2.5 0 0 1 6 9.5V9
               M15.5 4A3.5 3.5 0 0 1 19 7.5V16a4 4 0 0 1-4 4h-1v-8h1.5A2.5 2.5 0 0 0 18 9.5V9"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function DocIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5z"
        stroke="currentColor" strokeWidth="1.5" />
      <path d="M14 3v5h5M8 13h8M8 17h6M8 9h4"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

/* ---------- Features section (inline, unchanged) ---------- */
function Features() {
  const items = [
    { title: 'OCR for scanned PDFs', text: 'Extract text from images and scans with high accuracy.', accent: 'accent-violet', Icon: ScanIcon },
    { title: 'Citations & page refs', text: 'Summaries include page numbers for quick verification.', accent: 'accent-orange', Icon: CiteIcon },
    { title: 'Multi-language', text: 'Summarize and output in 25+ languages.', accent: 'accent-green', Icon: GlobeIcon },
    { title: 'Ask questions', text: 'Chat with your document and get quoted answers.', accent: 'accent-cyan', Icon: ChatIcon },
    { title: 'Bulk upload', text: 'Queue multiple PDFs and process them together.', accent: 'accent-pink', Icon: StackIcon },
    { title: 'Export & share', text: 'Download summaries as TXT/MD or copy to clipboard.', accent: 'accent-blue', Icon: ExportIcon },
  ];

  return (
    <section className="features">
      <h2 className="section-title">Power features, simple UX</h2>
      <p className="section-subtitle">Everything you need to go from long PDF to clear insight—fast.</p>
      <div className="feature-grid">
        {items.map(({ title, text, accent, Icon }) => (
          <div className="feature-card" key={title}>
            <div className={`feature-icon ${accent}`}><Icon /></div>
            <h3 className="feature-title">{title}</h3>
            <p className="feature-text">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
function ScanIcon(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/><rect x="14" y="3" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/><rect x="3" y="14" width="7" height="7" rx="2" stroke="currentColor" strokeWidth="1.5"/><path d="M14 18h7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>;}
function CiteIcon(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M8 6h9M8 10h9M8 14h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><circle cx="5" cy="6" r="1" fill="currentColor"/><circle cx="5" cy="10" r="1" fill="currentColor"/><circle cx="5" cy="14" r="1" fill="currentColor"/></svg>;}
function GlobeIcon(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5"/><path d="M3 12h18M12 3c-3 3.5-3 14.5 0 18 3-3.5 3-14.5 0-18z" stroke="currentColor" strokeWidth="1.5"/></svg>;}
function ChatIcon(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M7 17l-3 3V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H7z" stroke="currentColor" strokeWidth="1.5"/><path d="M8 8h8M8 12h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>;}
function StackIcon(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 3l9 5-9 5-9-5 9-5z" stroke="currentColor" strokeWidth="1.5"/><path d="M21 13l-9 5-9-5" stroke="currentColor" strokeWidth="1.5"/></svg>;}
function ExportIcon(){return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 16V4m0 0l-4 4m4-4l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><rect x="4" y="14" width="16" height="6" rx="2" stroke="currentColor" strokeWidth="1.5"/></svg>;}

/* ---------- Home pricing (inline, unchanged) ---------- */
function HomePricing() {
  const plans = [
    { id: 'starter', name: 'Starter', price: 499, features: ['1,000 pages/mo', 'Basic summaries', 'Limited Q&A'] },
    { id: 'pro', name: 'Pro', price: 899, features: ['10,000 pages/mo', 'Citations & refs', 'Advanced Q&A'] },
  ];
  const formatINR = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
  return (
    <section className="home-pricing">
      <h2 className="section-title">Simple pricing</h2>
      <p className="section-subtitle">Transparent monthly plans in INR.</p>
      <div className="home-price-grid">
        {plans.map((p, i) => (
          <div key={p.id} className={`home-price-card ${i === 1 ? 'highlight' : ''}`}>
            {i === 1 && <div className="home-price-badge">Most popular</div>}
            <div className="home-price-name">{p.name}</div>
            <div className="home-price-value">{formatINR(p.price)} <span className="per">/ month</span></div>
            <ul className="home-price-feats">
              {p.features.map((f) => (<li key={f}>• {f}</li>))}
            </ul>
            <a className={`btn ${i === 1 ? 'gradient' : 'outline'} btn--lg`} href="/signup">
              {i === 1 ? 'Upgrade to Pro' : 'Get Started'}
            </a>
          </div>
        ))}
      </div>
    </section>
  );
}