"use client";

import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { AddablePaper } from "@/lib/paper";
import { fetchAndStorePaperPdf, triggerBrowserFileDownload } from "@/lib/pdfDownloader";
import {
  ConnectedGraphNode,
  ConnectedGraphEdge,
  ConnectedGraphResponse,
} from "@/app/api/connected/route";
import {
  Search,
  ExternalLink,
  BookOpen,
  Download,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Play,
  Pause,
  HelpCircle,
  X,
  FileText,
  Network,
  AlertTriangle,
} from "lucide-react";

interface ConnectedGraphHubProps {
  onAddToNotebook?: (paper: AddablePaper) => void;
  initialSeed?: string;
}

interface SimNode extends ConnectedGraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

const EXAMPLE_SEEDS = [
  {
    label: "🍎 DeepFruits (Sensors 2016)",
    query: "DeepFruits: A Fruit Detection System Using Deep Neural Networks",
    doi: "10.3390/s16081222",
  },
  {
    label: "⚡ Transformers (NeurIPS 2017)",
    query: "Attention Is All You Need",
    doi: "10.48550/arXiv.1706.03762",
  },
  {
    label: "🧬 ResNet (CVPR 2016)",
    query: "Deep Residual Learning for Image Recognition",
    doi: "10.1109/CVPR.2016.90",
  },
  {
    label: "🔬 AlphaFold2 (Nature 2021)",
    query: "Highly accurate protein structure prediction with AlphaFold",
    doi: "10.1038/s41586-021-03819-2",
  },
];

export function ConnectedGraphHub({
  onAddToNotebook,
  initialSeed,
}: ConnectedGraphHubProps) {
  const [searchQuery, setSearchQuery] = useState(initialSeed || "DeepFruits: A Fruit Detection System Using Deep Neural Networks");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ message: string; seed?: string } | null>(null);
  const [graphData, setGraphData] = useState<ConnectedGraphResponse | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("");
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [showHowToRead, setShowHowToRead] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState<"graph" | "prior" | "derivative" | "list">("graph");
  const [physicsRunning, setPhysicsRunning] = useState(true);

  // Canvas Viewport transform (pan & zoom)
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const isDraggingCanvas = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });
  const draggedNode = useRef<SimNode | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const simNodesRef = useRef<SimNode[]>([]);
  const simEdgesRef = useRef<ConnectedGraphEdge[]>([]);
  const animFrameRef = useRef<number | null>(null);

  // Interpolate year color from light mint/teal (#a7d7c5) to deep emerald/pine (#1b4332)
  const getYearColor = (year: number, minYear: number, maxYear: number) => {
    const range = Math.max(1, maxYear - minYear);
    const t = Math.max(0, Math.min(1, (year - minYear) / range));
    // RGB interpolation
    // Start: [167, 215, 197] (Light Sage)
    // End:   [27, 67, 50]    (Deep Pine)
    const r = Math.round(167 + (27 - 167) * t);
    const g = Math.round(215 + (67 - 215) * t);
    const b = Math.round(197 + (50 - 197) * t);
    return `rgb(${r}, ${g}, ${b})`;
  };

  // Initialize nodes for force simulation
  const initializeSimulation = useCallback((data: ConnectedGraphResponse) => {
    const width = 800;
    const height = 600;
    const centerX = width / 2;
    const centerY = height / 2;

    const minYear = data.minYear || 2014;
    const maxYear = data.maxYear || 2024;

    const simNodes: SimNode[] = data.nodes.map((n, i) => {
      const isOrig = n.id === data.origin.id || n.isOrigin;
      // Citation-scaled radius
      const radius = isOrig ? 28 : Math.max(12, Math.min(30, 11 + Math.sqrt(n.citationCount || 0) * 0.55));
      const color = getYearColor(n.year, minYear, maxYear);

      // Angle distribution around center
      const angle = (i / Math.max(1, data.nodes.length - 1)) * 2 * Math.PI;
      const dist = isOrig ? 0 : 130 + Math.random() * 160;

      return {
        ...n,
        x: isOrig ? centerX : centerX + Math.cos(angle) * dist,
        y: isOrig ? centerY : centerY + Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        radius,
        color,
      };
    });

    simNodesRef.current = simNodes;
    simEdgesRef.current = data.edges;
    setTransform({ x: 0, y: 0, k: 1 });
  }, []);

  const fetchGraph = useCallback(async (term: string) => {
    if (!term.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/connected?q=${encodeURIComponent(term.trim())}`);
      const data = await res.json();
      if (!res.ok || data.error) {
        setError({
          message: data.error || `No citation network found for "${term.trim()}".`,
          seed: term.trim(),
        });
        setGraphData(null);
        return;
      }
      setGraphData(data);
      setSelectedNodeId(data.origin.id);
      initializeSimulation(data);
    } catch (err) {
      console.error("Failed to load connected graph:", err);
      setError({
        message: "Network error: Unable to connect to citation graph service.",
        seed: term.trim(),
      });
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  }, [initializeSimulation]);

  // Load the seeded graph once, on mount. Reading the seed from a ref keeps the
  // effect from refiring on every keystroke: `searchQuery` changes as the user
  // types, but only submitting the form should run a new search.
  const initialQueryRef = useRef(searchQuery);
  useEffect(() => {
    void fetchGraph(initialQueryRef.current);
  }, [fetchGraph]);

  // Render Canvas with High-DPI support
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
      canvas.width = width * dpr;
      canvas.height = height * dpr;
    }

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    // Apply viewport transform (pan & zoom)
    ctx.translate(transform.x + width / 2, transform.y + height / 2);
    ctx.scale(transform.k, transform.k);
    ctx.translate(-400, -300);

    const nodes = simNodesRef.current;
    const edges = simEdgesRef.current;
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));

    // Neighbors of active or hovered node
    const highlightId = hoveredNodeId || selectedNodeId;
    const neighborIds = new Set<string>();
    if (highlightId) {
      neighborIds.add(highlightId);
      for (const edge of edges) {
        if (edge.source === highlightId) neighborIds.add(edge.target);
        if (edge.target === highlightId) neighborIds.add(edge.source);
      }
    }

    // 1. Draw Edges
    for (const edge of edges) {
      const na = nodeMap.get(edge.source);
      const nb = nodeMap.get(edge.target);
      if (!na || !nb) continue;

      const isConnectedToHighlight =
        highlightId && (edge.source === highlightId || edge.target === highlightId);

      ctx.beginPath();
      ctx.moveTo(na.x, na.y);
      ctx.lineTo(nb.x, nb.y);

      if (isConnectedToHighlight) {
        ctx.strokeStyle = "rgba(45, 106, 79, 0.75)";
        ctx.lineWidth = 2.2;
      } else if (highlightId) {
        ctx.strokeStyle = "rgba(160, 174, 192, 0.15)";
        ctx.lineWidth = 0.8;
      } else {
        ctx.strokeStyle = "rgba(160, 174, 192, 0.35)";
        ctx.lineWidth = Math.max(0.9, (edge.weight || 0.5) * 2);
      }
      ctx.stroke();
    }

    // 2. Draw Nodes
    for (const node of nodes) {
      const isSelected = node.id === selectedNodeId;
      const isHovered = node.id === hoveredNodeId;
      const isHighlighted = !highlightId || neighborIds.has(node.id);
      const isOrig = !!node.isOrigin;

      ctx.save();

      // Opacity dimming for non-neighbors
      ctx.globalAlpha = isHighlighted ? 1.0 : 0.22;

      // Draw Outer Halo for Origin paper (Purple/Magenta as in Connected Papers)
      if (isOrig) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 6, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(147, 51, 234, 0.4)";
        ctx.lineWidth = 6;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 3, 0, Math.PI * 2);
        ctx.strokeStyle = "#9333ea";
        ctx.lineWidth = 2.5;
        ctx.stroke();
      }

      // Draw Selected Node Halo (Emerald)
      if (isSelected && !isOrig) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 4, 0, Math.PI * 2);
        ctx.strokeStyle = "#10b981";
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      // Draw Hover Halo
      if (isHovered) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 5, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(52, 211, 153, 0.8)";
        ctx.lineWidth = 2.5;
        ctx.stroke();
      }

      // Node Body Circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fillStyle = isOrig ? "#a855f7" : node.color;
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.8;
      ctx.stroke();

      // Text Label (e.g. "Sa, 2016", "Redmon, 2015")
      ctx.font = isOrig ? "bold 12px Inter, sans-serif" : isSelected ? "bold 11px Inter, sans-serif" : "10px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      // Label background pill
      const labelText = node.label || `${node.authors?.[0] || "Paper"}, ${node.year}`;
      const textWidth = ctx.measureText(labelText).width;

      ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
      ctx.beginPath();
      ctx.roundRect(node.x - textWidth / 2 - 4, node.y - node.radius - 17, textWidth + 8, 14, 4);
      ctx.fill();
      ctx.strokeStyle = "rgba(0, 0, 0, 0.1)";
      ctx.lineWidth = 0.5;
      ctx.stroke();

      ctx.fillStyle = "#1e293b";
      ctx.fillText(labelText, node.x, node.y - node.radius - 10);

      ctx.restore();
    }

    ctx.restore();
  }, [transform, hoveredNodeId, selectedNodeId]);

  // Force-directed simulation tick
  useEffect(() => {
    let lastTime = performance.now();

    const tick = (now: number) => {
      const dt = Math.min(32, now - lastTime) / 1000;
      lastTime = now;

      if (physicsRunning) {
        const nodes = simNodesRef.current;
        const edges = simEdgesRef.current;
        const width = 800;
        const height = 600;
        const centerX = width / 2;
        const centerY = height / 2;

        // 1. Coulomb repulsion between all node pairs
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const na = nodes[i];
            const nb = nodes[j];
            const dx = nb.x - na.x;
            const dy = nb.y - na.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const minDist = na.radius + nb.radius + 30;

            if (dist < 400) {
              const force = (12000 / (dist * dist)) * (dist < minDist ? 2.5 : 1);
              const fx = (dx / dist) * force;
              const fy = (dy / dist) * force;

              if (na !== draggedNode.current && !na.isOrigin) {
                na.vx -= fx * dt;
                na.vy -= fy * dt;
              }
              if (nb !== draggedNode.current && !nb.isOrigin) {
                nb.vx += fx * dt;
                nb.vy += fy * dt;
              }
            }
          }
        }

        // 2. Hooke's spring attraction along edges
        const nodeMap = new Map(nodes.map((n) => [n.id, n]));
        for (const edge of edges) {
          const na = nodeMap.get(edge.source);
          const nb = nodeMap.get(edge.target);
          if (na && nb) {
            const dx = nb.x - na.x;
            const dy = nb.y - na.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const targetDist = 90 + (1 - (edge.weight || 0.5)) * 140;
            const force = (dist - targetDist) * 1.8 * (edge.weight || 0.5);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (na !== draggedNode.current && !na.isOrigin) {
              na.vx += fx * dt;
              na.vy += fy * dt;
            }
            if (nb !== draggedNode.current && !nb.isOrigin) {
              nb.vx -= fx * dt;
              nb.vy -= fy * dt;
            }
          }
        }

        // 3. Center gravity pull towards center
        for (const n of nodes) {
          if (n.isOrigin) {
            n.x = centerX;
            n.y = centerY;
            n.vx = 0;
            n.vy = 0;
            continue;
          }
          if (n === draggedNode.current) continue;

          const dx = centerX - n.x;
          const dy = centerY - n.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          n.vx += (dx / dist) * 20 * dt;
          n.vy += (dy / dist) * 20 * dt;

          // Apply velocity with damping
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= 0.88;
          n.vy *= 0.88;
        }
      }

      renderCanvas();
      animFrameRef.current = requestAnimationFrame(tick);
    };

    animFrameRef.current = requestAnimationFrame(tick);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [physicsRunning, hoveredNodeId, selectedNodeId, transform, renderCanvas]);

  // Convert canvas client mouse coordinates to simulation world coordinates
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const width = canvas.clientWidth;
    const height = canvas.clientHeight;

    const worldX = (mouseX - (transform.x + width / 2)) / transform.k + 400;
    const worldY = (mouseY - (transform.y + height / 2)) / transform.k + 300;

    return { x: worldX, y: worldY };
  };

  // Mouse interaction: Hover, Click, Drag
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e);
    const nodes = simNodesRef.current;

    // Check if clicked a node
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = coords.x - n.x;
      const dy = coords.y - n.y;
      if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 4) {
        draggedNode.current = n;
        setSelectedNodeId(n.id);
        return;
      }
    }

    // Otherwise, pan canvas
    isDraggingCanvas.current = true;
    dragStart.current = { x: e.clientX - transform.x, y: e.clientY - transform.y };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoords(e);

    if (draggedNode.current) {
      draggedNode.current.x = coords.x;
      draggedNode.current.y = coords.y;
      draggedNode.current.vx = 0;
      draggedNode.current.vy = 0;
      return;
    }

    if (isDraggingCanvas.current) {
      setTransform((prev) => ({
        ...prev,
        x: e.clientX - dragStart.current.x,
        y: e.clientY - dragStart.current.y,
      }));
      return;
    }

    // Hover detection
    const nodes = simNodesRef.current;
    let foundHover: string | null = null;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = coords.x - n.x;
      const dy = coords.y - n.y;
      if (Math.sqrt(dx * dx + dy * dy) <= n.radius + 4) {
        foundHover = n.id;
        break;
      }
    }
    setHoveredNodeId(foundHover);
  };

  const handleMouseUp = () => {
    draggedNode.current = null;
    isDraggingCanvas.current = false;
  };

  // Zoom on wheel with non-passive listener to avoid browser console violations
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      setTransform((prev) => ({
        ...prev,
        k: Math.max(0.35, Math.min(3.5, prev.k * zoomFactor)),
      }));
    };

    canvas.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      canvas.removeEventListener("wheel", onWheel);
    };
  }, []);

  // Zoom buttons
  const handleZoom = (factor: number) => {
    setTransform((prev) => ({
      ...prev,
      k: Math.max(0.35, Math.min(3.5, prev.k * factor)),
    }));
  };

  const handleResetView = () => {
    setTransform({ x: 0, y: 0, k: 1 });
  };

  // Find currently selected node
  const selectedNode = useMemo(() => {
    if (!graphData) return null;
    return (
      graphData.nodes.find((n) => n.id === selectedNodeId) || graphData.origin
    );
  }, [graphData, selectedNodeId]);

  // Sorted list of papers for the left list
  const sortedConnectedPapers = useMemo(() => {
    if (!graphData) return [];
    return [...graphData.nodes].sort((a, b) => {
      if (a.isOrigin) return -1;
      if (b.isOrigin) return 1;
      return (b.similarityToOrigin || 0) - (a.similarityToOrigin || 0);
    });
  }, [graphData]);

  return (
    <div className="w-full space-y-4 animate-fade-in-up">
      {/* =========================================================================
          TOP SEED INPUT BAR & SEMINAL EXAMPLES
      ========================================================================= */}
      <div className="fernly-card p-4 sm:p-5 rounded-[2rem] border border-[var(--card-bdr)] flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            fetchGraph(searchQuery);
          }}
          className="flex-1 flex items-center gap-2"
        >
          <div className="relative flex-1 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--ink-muted)] group-focus-within:text-[var(--g-600)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search paper by title or DOI to map Connected Papers..."
              className="fernly-input w-full !pl-11 !pr-4 py-2.5 rounded-full text-xs sm:text-sm text-[var(--ink)] placeholder-[var(--ink-muted)]"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !searchQuery.trim()}
            className="btn-fernly-primary px-5 py-2.5 rounded-full text-xs font-bold disabled:opacity-50 cursor-pointer flex-shrink-0 flex items-center gap-1.5"
          >
            {loading ? "Mapping..." : "Map Graph 🚀"}
          </button>
        </form>

        {/* Quick Example Chips */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none flex-shrink-0">
          <span className="text-[11px] font-semibold text-[var(--ink-muted)] hidden lg:inline mr-1">
            Seminal Seeds:
          </span>
          {EXAMPLE_SEEDS.map((ex) => (
            <button
              key={ex.label}
              onClick={() => {
                setSearchQuery(ex.query);
                fetchGraph(ex.query);
              }}
              className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-[var(--panel)] hover:bg-[var(--card)] border border-[var(--card-bdr)] hover:border-[var(--g-500)] text-[var(--ink)] whitespace-nowrap cursor-pointer transition-all shadow-2xs"
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      {/* Visual Error / Fallback Banner */}
      {error && (
        <div className="fernly-card p-6 rounded-[2rem] border border-amber-300 dark:border-amber-700/60 bg-amber-50/70 dark:bg-amber-950/20 text-[var(--ink)] space-y-3 animate-fade-in mb-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 rounded-2xl bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 flex-shrink-0">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div className="flex-1 space-y-1.5">
              <h3 className="text-sm font-bold text-amber-900 dark:text-amber-200">
                Citation Network Unavailable
              </h3>
              <p className="text-xs text-amber-800/90 dark:text-amber-300/90 leading-relaxed font-medium">
                {error.message}
              </p>
              <div className="pt-2 text-xs text-[var(--ink-muted)] space-y-1">
                <p className="font-semibold text-[var(--ink)]">Suggested recovery steps:</p>
                <ul className="list-disc pl-4 space-y-0.5">
                  <li>Verify the paper title or search using its registered DOI (e.g., <code>10.1038/...</code>).</li>
                  <li>Use the <strong>Academic Search Hub</strong> to verify if the paper exists across OpenAlex or Crossref.</li>
                  <li>Or explore one of the verified seminal benchmark graphs:</li>
                </ul>
              </div>
              <div className="pt-2 flex flex-wrap gap-2">
                {EXAMPLE_SEEDS.map((ex) => (
                  <button
                    key={ex.label}
                    onClick={() => {
                      setSearchQuery(ex.query);
                      fetchGraph(ex.query);
                    }}
                    className="px-3 py-1.5 rounded-full text-xs font-semibold bg-white dark:bg-amber-900/40 border border-amber-300 dark:border-amber-700 hover:border-amber-500 text-amber-900 dark:text-amber-200 transition-all cursor-pointer shadow-xs"
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-amber-700/70 hover:text-amber-900 dark:text-amber-400 dark:hover:text-amber-200 p-1 rounded-lg cursor-pointer transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* =========================================================================
          THREE-COLUMN CONNECTED PAPERS LAYOUT (Matches connectedpapers.com)
      ========================================================================= */}
      {graphData && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[780px] min-h-[700px]">
          
          {/* =====================================================================
              LEFT PANEL: ORIGIN & CONNECTED PAPERS LIST
          ===================================================================== */}
          <div className="lg:col-span-3 fernly-card p-4 rounded-[2rem] border border-[var(--card-bdr)] flex flex-col h-full overflow-hidden">
            {/* Origin Paper Card Header */}
            <div
              onClick={() => setSelectedNodeId(graphData.origin.id)}
              className={`p-3.5 rounded-2xl border transition-all cursor-pointer mb-3 flex-shrink-0 ${
                selectedNodeId === graphData.origin.id
                  ? "border-purple-400 dark:border-purple-600 bg-purple-50/40 dark:bg-purple-950/20"
                  : "border-purple-200 dark:border-purple-900/50 bg-[var(--panel)] hover:border-purple-400"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-800">
                  Origin paper
                </span>
                <span className="text-[10px] font-bold text-purple-600 font-mono">
                  {graphData.origin.citationCount} cites
                </span>
              </div>
              <h4 className="text-xs font-bold text-[var(--ink)] line-clamp-2 leading-snug">
                {graphData.origin.title}
              </h4>
              <p className="text-[10px] text-[var(--ink-muted)] mt-1 truncate">
                {graphData.origin.authors?.slice(0, 2).join(", ")} · {graphData.origin.year}
              </p>
            </div>

            {/* Subheader */}
            <div className="flex items-center justify-between px-1 mb-2 flex-shrink-0">
              <span className="text-[11px] font-bold text-[var(--ink-muted)] uppercase tracking-wider">
                Similar Papers ({graphData.nodes.length - 1})
              </span>
              <span className="text-[10px] text-[var(--ink-muted)] font-mono">
                Similarity ranked
              </span>
            </div>

            {/* Scrollable Connected Papers List */}
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 scrollbar-thin">
              {sortedConnectedPapers
                .filter((p) => p.id !== graphData.origin.id)
                .map((paper) => {
                  const isSelected = paper.id === selectedNodeId;
                  const isHovered = paper.id === hoveredNodeId;

                  return (
                    <div
                      key={paper.id}
                      onClick={() => setSelectedNodeId(paper.id)}
                      onMouseEnter={() => setHoveredNodeId(paper.id)}
                      onMouseLeave={() => setHoveredNodeId(null)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer text-xs ${
                        isSelected
                          ? "border-[var(--g-500)] bg-[var(--g-50)]/40 dark:bg-[var(--g-950)]/40 shadow-xs"
                          : isHovered
                          ? "border-[var(--card-bdr)] bg-[var(--panel)]"
                          : "border-transparent hover:border-[var(--card-bdr)] hover:bg-[var(--panel)]/60"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h5 className="font-semibold text-[var(--ink)] line-clamp-2 leading-tight flex-1">
                          {paper.title}
                        </h5>
                        <span className="text-[11px] font-bold text-[var(--ink-muted)] font-mono flex-shrink-0">
                          {paper.year}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1 text-[10px] text-[var(--ink-muted)]">
                        <span className="truncate max-w-[140px]">
                          {paper.authors?.[0] || "Author"}
                          {paper.authors && paper.authors.length > 1 ? " et al." : ""}
                        </span>
                        <span className="font-mono text-emerald-700 dark:text-emerald-400 font-semibold">
                          {Math.round((paper.similarityToOrigin || 0.8) * 100)}% match
                        </span>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* =====================================================================
              CENTER PANEL: INTERACTIVE FORCE GRAPH CANVAS
          ===================================================================== */}
          <div className="lg:col-span-6 fernly-card p-0 rounded-[2rem] border border-[var(--card-bdr)] flex flex-col h-full relative overflow-hidden bg-[var(--panel)]">
            {/* Top Toolbar / Title & Sub-tabs */}
            <div className="p-4 border-b border-[var(--card-bdr)] bg-[var(--card)] flex items-center justify-between gap-3 z-10 flex-shrink-0">
              <div className="min-w-0 flex-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--ink-muted)] block">
                  Connected Graph
                </span>
                <h3 className="text-xs sm:text-sm font-bold text-[var(--ink)] truncate">
                  {graphData.origin.title}
                </h3>
              </div>

              {/* Sub-nav tabs */}
              <div className="flex items-center gap-1 flex-shrink-0">
                <button
                  onClick={() => setActiveSubTab("graph")}
                  className={`px-3 py-1 rounded-full text-[11px] font-semibold transition-all cursor-pointer ${
                    activeSubTab === "graph"
                      ? "btn-fernly-primary !py-1 !text-[11px]"
                      : "btn-fernly-ghost !py-1 !text-[11px]"
                  }`}
                >
                  Graph view
                </button>
                <button
                  onClick={() => setActiveSubTab("prior")}
                  className={`px-3 py-1 rounded-full text-[11px] font-semibold transition-all cursor-pointer ${
                    activeSubTab === "prior"
                      ? "btn-fernly-primary !py-1 !text-[11px]"
                      : "btn-fernly-ghost !py-1 !text-[11px]"
                  }`}
                >
                  Prior works ({graphData.priorWorksCount || 12})
                </button>
                <button
                  onClick={() => setActiveSubTab("derivative")}
                  className={`px-3 py-1 rounded-full text-[11px] font-semibold transition-all cursor-pointer ${
                    activeSubTab === "derivative"
                      ? "btn-fernly-primary !py-1 !text-[11px]"
                      : "btn-fernly-ghost !py-1 !text-[11px]"
                  }`}
                >
                  Derivative ({graphData.derivativeWorksCount || 24})
                </button>
              </div>
            </div>

            {/* Interactive Viewport (Graph canvas or Prior/Derivative works list) */}
            {activeSubTab === "graph" ? (
              <div className="flex-1 relative w-full h-full cursor-grab active:cursor-grabbing overflow-hidden">
                <canvas
                  ref={canvasRef}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  className="w-full h-full block select-none"
                />

                {/* Floating "How to read the graph" card (Exact match to connected papers) */}
                {showHowToRead && (
                  <div className="absolute top-4 left-4 max-w-xs p-4 rounded-2xl bg-[var(--card)]/95 backdrop-blur-md border border-[var(--card-bdr)] shadow-lg text-xs space-y-2 z-20 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[var(--ink)] flex items-center gap-1.5">
                        <HelpCircle className="h-4 w-4 text-[var(--g-600)]" />
                        <span>How to read the graph</span>
                      </span>
                      <button
                        onClick={() => setShowHowToRead(false)}
                        className="text-[var(--ink-muted)] hover:text-[var(--ink)] p-0.5 rounded cursor-pointer"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <p className="text-[11px] text-[var(--ink-muted)] leading-relaxed">
                      Each node is an academic paper related to the origin paper:
                    </p>
                    <ul className="text-[11px] text-[var(--ink)] space-y-1 list-disc pl-4 leading-relaxed font-medium">
                      <li>Papers are arranged according to their similarity (not a citation tree).</li>
                      <li><strong className="text-[var(--g-700)] dark:text-[var(--g-300)]">Node size</strong> is the number of citations.</li>
                      <li><strong className="text-[var(--g-700)] dark:text-[var(--g-300)]">Node color</strong> is the publishing year.</li>
                      <li>Similar papers have strong connecting lines and cluster together.</li>
                    </ul>
                  </div>
                )}

                {/* Toggle to reopen "How to read" if closed */}
                {!showHowToRead && (
                  <button
                    onClick={() => setShowHowToRead(true)}
                    className="absolute top-4 left-4 p-2 rounded-xl bg-[var(--card)]/90 backdrop-blur-sm border border-[var(--card-bdr)] text-[var(--ink-muted)] hover:text-[var(--ink)] shadow-xs z-10 cursor-pointer"
                    title="How to read the graph"
                  >
                    <HelpCircle className="h-4 w-4" />
                  </button>
                )}

                {/* Bottom-Left: Zoom & Physics Controls */}
                <div className="absolute bottom-4 left-4 flex items-center gap-1.5 bg-[var(--card)]/90 backdrop-blur-sm p-1.5 rounded-2xl border border-[var(--card-bdr)] shadow-md z-20">
                  <button
                    onClick={() => handleZoom(1.2)}
                    className="p-1.5 rounded-xl hover:bg-[var(--panel)] text-[var(--ink)] cursor-pointer"
                    title="Zoom In"
                  >
                    <ZoomIn className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleZoom(0.83)}
                    className="p-1.5 rounded-xl hover:bg-[var(--panel)] text-[var(--ink)] cursor-pointer"
                    title="Zoom Out"
                  >
                    <ZoomOut className="h-4 w-4" />
                  </button>
                  <button
                    onClick={handleResetView}
                    className="p-1.5 rounded-xl hover:bg-[var(--panel)] text-[var(--ink)] cursor-pointer"
                    title="Reset View / Fit to Screen"
                  >
                    <Maximize2 className="h-4 w-4" />
                  </button>
                  <div className="h-4 w-px bg-[var(--card-bdr)]" />
                  <button
                    onClick={() => setPhysicsRunning(!physicsRunning)}
                    className={`p-1.5 rounded-xl cursor-pointer ${
                      physicsRunning ? "text-emerald-600" : "text-amber-600"
                    }`}
                    title={physicsRunning ? "Pause Physics Simulation" : "Resume Physics Simulation"}
                  >
                    {physicsRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </button>
                </div>

                {/* Bottom-Right: Year Color Bar Legend */}
                <div className="absolute bottom-4 right-4 flex items-center gap-2 bg-[var(--card)]/90 backdrop-blur-sm p-2 px-3 rounded-2xl border border-[var(--card-bdr)] shadow-md z-20 text-[10px] font-mono font-semibold">
                  <span className="text-[var(--ink-muted)]">{graphData.minYear || 2014}</span>
                  <div
                    className="w-24 h-2.5 rounded-full border border-black/10 dark:border-white/10 shadow-2xs"
                    style={{
                      background:
                        "linear-gradient(to right, rgb(167, 215, 197), rgb(82, 183, 136), rgb(27, 67, 50))",
                    }}
                    title="Node color represents publishing year"
                  />
                  <span className="text-[var(--ink)]">{graphData.maxYear || 2024}</span>
                </div>
              </div>
            ) : (
              /* PRIOR WORKS & DERIVATIVE WORKS LIST VIEW */
              <div className="flex-1 overflow-y-auto p-5 space-y-3.5 scrollbar-thin bg-[var(--panel)]">
                <div className="p-3.5 rounded-2xl bg-[var(--card)] border border-[var(--card-bdr)] flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-[var(--ink)] flex items-center gap-1.5">
                      <span>{activeSubTab === "prior" ? "📚 Foundational Prior Works" : "🚀 Derivative Breakthrough Works"}</span>
                    </h4>
                    <p className="text-[11px] text-[var(--ink-muted)] mt-0.5">
                      {activeSubTab === "prior"
                        ? "These papers were cited most often by the papers in the graph. Foundational ancestry of the field."
                        : "These papers cited the papers in the graph most often. Milestone descendants and recent expansions."}
                    </p>
                  </div>
                  <span className="fernly-badge fernly-badge-leaf text-xs font-mono font-bold flex-shrink-0">
                    {activeSubTab === "prior"
                      ? `${(graphData.priorWorks || graphData.nodes.filter(n => !n.isOrigin && n.year <= graphData.origin.year)).length} papers`
                      : `${(graphData.derivativeWorks || graphData.nodes.filter(n => !n.isOrigin && n.year > graphData.origin.year)).length} papers`}
                  </span>
                </div>

                <div className="space-y-2">
                  {(activeSubTab === "prior"
                    ? (graphData.priorWorks || graphData.nodes.filter((n) => !n.isOrigin && n.year <= graphData.origin.year))
                    : (graphData.derivativeWorks || graphData.nodes.filter((n) => !n.isOrigin && n.year > graphData.origin.year))
                  ).map((paper) => {
                    const isSelected = paper.id === selectedNodeId;
                    return (
                      <div
                        key={paper.id}
                        onClick={() => setSelectedNodeId(paper.id)}
                        className={`p-4 rounded-2xl border transition-all cursor-pointer text-xs ${
                          isSelected
                            ? "border-[var(--g-500)] bg-[var(--card)] shadow-xs"
                            : "border-[var(--card-bdr)] bg-[var(--card)]/60 hover:bg-[var(--card)] hover:border-[var(--g-400)]"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <span className="text-[10px] font-bold text-[var(--ink-muted)] font-mono block mb-0.5">
                              {paper.venue || "Journal"} · {paper.year}
                            </span>
                            <h5 className="font-bold text-[var(--ink)] text-xs sm:text-sm line-clamp-2 leading-snug">
                              {paper.title}
                            </h5>
                            <p className="text-[11px] text-[var(--ink-muted)] mt-1 truncate">
                              {paper.authors?.slice(0, 3).join(", ")}
                              {paper.authors && paper.authors.length > 3 ? " et al." : ""}
                            </p>
                          </div>
                          <div className="flex flex-col items-end gap-1 flex-shrink-0">
                            <span className="fernly-badge fernly-badge-neutral text-[10px] font-mono font-semibold">
                              {paper.citationCount} cites
                            </span>
                            <span className="text-[10px] text-emerald-700 dark:text-emerald-400 font-semibold font-mono">
                              {Math.round((paper.similarityToOrigin || 0.8) * 100)}% match
                            </span>
                          </div>
                        </div>

                        {paper.abstract && (
                          <p className="mt-2 text-[11px] text-[var(--ink-muted)] line-clamp-2 leading-relaxed bg-[var(--panel)] p-2.5 rounded-xl border border-[var(--card-bdr)]">
                            {paper.abstract}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* =====================================================================
              RIGHT PANEL: SELECTED PAPER DEEP DETAIL INSPECTOR
          ===================================================================== */}
          <div className="lg:col-span-3 fernly-card p-5 rounded-[2rem] border border-[var(--card-bdr)] flex flex-col h-full overflow-hidden">
            {selectedNode ? (
              <div className="flex flex-col h-full space-y-4">
                {/* Paper Header & Badges */}
                <div className="space-y-2 flex-shrink-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-[var(--panel)] border border-[var(--card-bdr)] text-[10px] font-semibold text-[var(--g-700)] dark:text-[var(--g-300)]">
                      {selectedNode.isOrigin ? "Origin Paper" : "Connected Cluster Paper"}
                    </span>
                    <span className="fernly-badge fernly-badge-leaf text-[10px] font-mono font-bold">
                      {selectedNode.citationCount || 0} Citations
                    </span>
                  </div>

                  <h3 className="text-sm sm:text-base font-bold text-[var(--ink)] leading-snug tracking-tight">
                    {selectedNode.title}
                  </h3>

                  <p className="text-xs text-[var(--ink-muted)] font-medium">
                    {selectedNode.authors?.join(", ")}
                  </p>

                  <div className="flex items-center gap-2 text-[11px] text-[var(--ink-muted)]">
                    <span className="font-semibold text-[var(--ink)]">{selectedNode.year}</span>
                    <span>·</span>
                    <span className="italic truncate">{selectedNode.venue || "Academic Proceedings"}</span>
                  </div>
                </div>

                {/* Action Buttons: Save to Notebook / PDF Download */}
                <div className="space-y-2 pt-2 border-t border-[var(--card-bdr)] flex-shrink-0">
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => onAddToNotebook?.(selectedNode)}
                      className="btn-fernly-primary py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 shadow-xs"
                    >
                      <BookOpen className="h-3.5 w-3.5" />
                      <span>Notebook</span>
                    </button>

                    <button
                      onClick={async () => {
                        const res = await fetchAndStorePaperPdf(
                          { doi: selectedNode.doi, title: selectedNode.title, pdfUrl: selectedNode.pdfUrl }
                        );
                        if (res.success && res.blob) {
                          triggerBrowserFileDownload(res.blob, selectedNode.title);
                        } else if (res.landingUrl) {
                          window.open(res.landingUrl, "_blank");
                        }
                      }}
                      className="btn-fernly-ghost py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 border border-[var(--card-bdr)] shadow-xs"
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>PDF</span>
                    </button>
                  </div>

                  {/* Re-center Graph Action */}
                  {!selectedNode.isOrigin && (
                    <button
                      onClick={() => {
                        setSearchQuery(selectedNode.doi || selectedNode.title);
                        fetchGraph(selectedNode.doi || selectedNode.title);
                      }}
                      className="w-full py-2 px-3 rounded-xl text-xs font-semibold bg-purple-50 dark:bg-purple-950/30 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 hover:bg-purple-100 flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                    >
                      <Network className="h-3.5 w-3.5" />
                      <span>Build graph from this paper</span>
                    </button>
                  )}
                </div>

                {/* External Discovery Links */}
                <div className="flex items-center gap-2 pt-1 border-t border-[var(--card-bdr)] flex-shrink-0 text-xs">
                  {selectedNode.doi && (
                    <a
                      href={`https://doi.org/${selectedNode.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1 rounded-lg bg-[var(--panel)] border border-[var(--card-bdr)] text-[var(--g-600)] hover:underline flex items-center gap-1 font-mono text-[10px]"
                    >
                      <span>DOI</span>
                      <ExternalLink className="h-2.5 w-2.5" />
                    </a>
                  )}

                  <a
                    href={`https://scholar.google.com/scholar?q=${encodeURIComponent(selectedNode.title)}`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-2.5 py-1 rounded-lg bg-[var(--panel)] border border-[var(--card-bdr)] text-[var(--ink-muted)] hover:text-[var(--ink)] flex items-center gap-1 text-[10px]"
                  >
                    <span>Google Scholar</span>
                    <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                </div>

                {/* Abstract Text Canvas */}
                <div className="flex-1 overflow-y-auto space-y-2 pr-1 pt-1 border-t border-[var(--card-bdr)] scrollbar-thin">
                  <span className="text-[10px] font-bold text-[var(--ink-muted)] uppercase tracking-wider block">
                    Abstract
                  </span>
                  <p className="text-xs text-[var(--ink)] leading-relaxed select-text font-sans">
                    {selectedNode.abstract || "No detailed abstract text recorded."}
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center text-[var(--ink-muted)] space-y-2">
                <FileText className="h-8 w-8 opacity-40" />
                <p className="text-xs">Select any node on the graph to inspect its citation impact and abstract.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
