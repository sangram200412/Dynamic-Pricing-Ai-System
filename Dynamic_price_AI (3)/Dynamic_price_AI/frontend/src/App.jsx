import React, { useState, useRef } from 'react';

const API_BASE = "http://localhost:8000";

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [identifying, setIdentifying] = useState(false);
  const [product, setProduct] = useState(null);
  const [platforms, setPlatforms] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState("SYSTEM_IDLE // AWAITING_TELEMETRY");
  const [scanTime, setScanTime] = useState(0);

  const fileInputRef = useRef(null);

  const parsePrice = (value) => {
    if (typeof value === 'number') return value;
    if (!value) return 0;
    const numeric = String(value).replace(/[^\d.]/g, '');
    return numeric ? Number(numeric) : 0;
  };

  const volatilityNodes = (platforms.length > 0 ? platforms : [...Array(7)].map((_, i) => ({
    platform: `NODE_${i + 1}`,
    price_formatted: "N/A",
    product_count: 0
  }))).map((node) => {
    const price = parsePrice(node?.best_price ?? node?.price_raw ?? node?.price ?? node?.price_formatted);
    return { ...node, _priceValue: price };
  });

  const maxVolatilityPrice = Math.max(...volatilityNodes.map((n) => n._priceValue), 1);

  const resetSession = () => {
    setFile(null);
    setPreview(null);
    setProduct(null);
    setPlatforms([]);
    setAnalysis(null);
    setScanTime(0);
    setStatus("SYSTEM_IDLE // AWAITING_TELEMETRY");
  };

  const handleFileSelect = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setStatus("ASSET_LOADED // READY_FOR_SCAN");
  };

  const executeScan = async () => {
    if (!file) return;
    setIdentifying(true);
    setStatus("NEURAL_SCANNING...");
    const start = Date.now();

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setProduct({
        name: data.product_name,
        brand: data.brand || "Unknown",
        category: data.category || "General",
        confidence: data.confidence || 0.95
      });
      setPlatforms(Object.values(data.platforms || {}));
      setAnalysis(data.ml_analysis || {});
      setScanTime(((Date.now() - start) / 1000).toFixed(1));
      setStatus("SURVEILLANCE_COMPLETE");
    } catch (err) {
      setStatus("PROTOCOL_ERROR");
    } finally {
      setIdentifying(false);
    }
  };

  return (
    <div className="app-ultra">
      {/* ── BACKGROUND FX ── */}
      <div className="noise" />
      <div className="stars" />

      {/* ── STICKY HUD NAVIGATION ── */}
      <nav className="nav-glass">
        <div className="logo-wrap">
          <div className="logo-icon">Ψ</div>
          <div className="title-wrap">
            <h1>PRICESCOPE ◈ INTELLIGENCE</h1>
            <p>Advanced Real-Time Market Surveillance</p>
          </div>
        </div>
        <div className="system-status">
          <div className="spinner-mini" style={{opacity: identifying ? 1 : 0}} />
          <span className="mono">{status} {scanTime > 0 ? `// ${scanTime}s` : ""}</span>
        </div>
      </nav>

      <main className="main-container">
        {/* ── INPUT_SOURCE CARD ── */}
        <div className="glass-card animate-up">
          <span className="label-mini">INPUT_SOURCE</span>
          <div className="drop-zone" onClick={() => fileInputRef.current.click()}>
            <input type="file" hidden ref={fileInputRef} onChange={handleFileSelect} />
            {preview ? (
              <img src={preview} className="preview-img" alt="Target" />
            ) : (
              <div style={{opacity: 0.2, textAlign: 'center'}}>
                <div style={{fontSize: '40px'}}>+</div>
                <span>LOAD_TARGET_ASSET</span>
              </div>
            )}
          </div>
          <div style={{display: 'flex', gap: '10px', marginTop: '20px'}}>
            <button className="btn-glow" style={{flex: 1}} onClick={preview ? executeScan : () => fileInputRef.current.click()}>
              {preview ? (identifying ? "SCANNING..." : "SCAN THIS IMAGE") : "LOAD_TARGET"}
            </button>
            {preview && <button className="btn-glow" style={{flex: 0.3, background: 'rgba(255, 51, 102, 0.2)', border: '1px solid #ff3366', color: '#ff3366'}} onClick={resetSession}>CLEAR</button>}
          </div>
        </div>

        {/* ── TARGET_IDENTIFICATION CARD ── */}
        <div className="glass-card animate-up">
          <span className="label-mini">TARGET_IDENTIFICATION</span>
          <h2 className="product-title">{product?.name || "Awaiting Identification..."}</h2>
          
          <div className="meta-grid">
            <div className="meta-item">
              <b>MANUFACTURER</b>
              <span>{product?.brand || "---"}</span>
            </div>
            <div className="meta-item">
              <b>MARKET CLUSTER</b>
              <span>{product?.category || "---"}</span>
            </div>
            <div className="meta-item">
              <b>CONFIDENCE</b>
              <span style={{color: 'var(--accent-cyan)'}}>{product ? (product.confidence * 100).toFixed(0) : 0}% MATCH</span>
            </div>
            <div className="meta-item">
              <b>NEURAL_KEYS</b>
              <span>{platforms.length} Points</span>
            </div>
          </div>
          
          <div style={{marginTop: '30px'}}>
            <span className="label-mini">SEARCH_VECTORS</span>
            <div style={{background: 'rgba(255,255,255,0.03)', padding: '15px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)'}}>
              <span className="mono" style={{fontSize: '11px', opacity: 0.5}}>• {product?.name || "No vectors identified."}</span>
            </div>
          </div>
        </div>

        {/* ── MARKET_NODES (PLATFORMS) ── */}
        <div className="platform-row animate-up">
          {(platforms.length > 0 ? platforms : [...Array(5)]).map((p, i) => (
            <div key={i} className={`platform-card ${i === 3 ? 'active-deal' : ''}`}>
              <div className="p-icon">{p?.platform?.charAt(0) || "?"}</div>
              <span className="label-mini" style={{fontSize: '9px', marginBottom: '8px'}}>{p?.platform || "DATA_NODE"}</span>
              <div className="p-price">{p?.price_formatted || p?.price || "₹0.00"}</div>
              <div className="p-reviews">DATA_NODE: {p?.product_count || 0} ITEMS</div>
              <button 
                className="btn-intercept"
                onClick={() => p?.url && window.open(p.url, '_blank')}
                style={{ cursor: p?.url ? 'pointer' : 'not-allowed' }}
              >
                INTERCEPT_URL
              </button>
            </div>
          ))}
        </div>

        {/* ── VIZ & RECS HUD ── */}
        <div className="viz-recs-area animate-up">
          <div className="glass-card chart-card">
            <span className="label-mini">MARKET_VOLATILITY_BAND</span>
            <div className="bar-container">
              {volatilityNodes.map((node, i) => (
                <div key={`${node?.platform || 'NODE'}-${i}`} className="bar-wrap">
                  <div
                    className="bar"
                    style={{
                      height: `${node._priceValue > 0 ? Math.max(18, (node._priceValue / maxVolatilityPrice) * 100) : 12}%`,
                      opacity: node._priceValue > 0 ? 0.9 : 0.2
                    }}
                  />
                  <span style={{fontSize: '9px', opacity: 0.45, marginTop: '8px'}}>
                    {node?.platform || `NODE_${i + 1}`}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card">
            <span className="label-mini">NEURAL_PRICE_OPTIMIZATION</span>
            <div className="rec-price" style={{color: 'var(--accent-green)', fontSize: '54px'}}>
               {analysis?.recommended_price ? `₹${analysis.recommended_price.toLocaleString()}` : "₹000.00"}
            </div>
            <div className="strategy-pill">ACTIVE.STRATEGY: COMPETITIVE</div>
            <div className="expl-box">
              {analysis?.explanation || "Awaiting market surveillance data to formulate optimal target strategy."}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;